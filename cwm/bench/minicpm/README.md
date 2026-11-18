# MiniCPM5 trained on TypeScript debugger pauses

A rank-eight LoRA on [openbmb/MiniCPM5-1B](https://huggingface.co/openbmb/MiniCPM5-1B/tree/ac83f813ba7da263c51a9f3ec37c2072597e54af) produced one completely correct next pause on 34 held-out transitions. Of its 25 outputs within the CSV and numeric domain, six pointed outside the supplied source. The unmodified release produced zero rows within the domain under the same prompt. Both missed the new local values on all 12 writes.

| Fresh-source metric                 | Original weights | Trace-trained LoRA |
| ----------------------------------- | ---------------: | -----------------: |
| Complete next frame                 |             0/34 |               1/34 |
| CSV and numeric domain              |             0/34 |              25/34 |
| Within domain and inside source     |             0/34 |              19/34 |
| Event, line and column together     |             0/34 |              10/34 |
| Both locals                         |             0/34 |               3/34 |
| Both locals when either changed     |             0/12 |               0/12 |
| Target-token NLL, nats (364 tokens) |          1.43134 |            0.70256 |

Each forecast starts from an observed frame. Returning the current locals unchanged would score 22/34 on the locals column. The sole exact prediction was a loop exit with unchanged locals. On the addition body with `(2,3)`, the adapter correctly emitted a step at 3:1 but forecast locals `(2,4)`. V8 showed `(5,3)`. Exact frames by body were 0/6 (addition), 0/7 (branch), 1/12 (loop), and 0/9 (two writes). These four programs and three inputs per program are the units behind the 34 dependent transitions. This run measured neither editing quality nor uninterrupted execution.

## Prompt the weights

From this directory on a CPU machine with Python 3.11, create an environment once:

```sh
python3.11 -m venv ~/.venvs/minicpm-cwm
. ~/.venvs/minicpm-cwm/bin/activate
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.7.1
python -m pip install -r requirements.txt
python prompt.py --text 'Write a TypeScript function that sums two integers.' --max-new-tokens 192
```

In a free-form smoke test, the adapter answered this request with a typed `sumIntegers` function returning `a + b`. For a next-pause prompt, supply the exact source bytes and current observation. The expected format is `S,line,column,x,y` or `R,line,column,x,y,returnValue`. The command prints the model's greedy completion. It does not execute the file. Add `--base` to use the original weights.

```sh
printf '%s\n%s\n%s\n%s' 'export function run(x:number, y:number) {' 'x = x + y;' 'return x - y;' '}' > /tmp/mini-example.ts
python prompt.py --source /tmp/mini-example.ts --current 'S,2,1,2,3'
```

The loader pins the release revision shown above. The first call downloads approximately 2.16 GB of BF16 weights and loads them in FP32 for CPU inference. To use a downloaded copy, set `CWM_MODEL_PATH` to the local snapshot directory. Local loading copies the eight release files into a temporary directory, checks their digests there, and loads the tokenizer and model offline from those copies. Allow 2.2 GB of temporary disk space during loading. Use `CWM_THREADS` to change the default of eight CPU threads. Both coding and pause prompts use the same PEFT weights in `adapter/`.

### Check the stock template and checkpoint

With the verified snapshot on disk, run the integration tests from this directory. To include the server check, start [the b6602 Q8 server](../../PROMPTING.md#local-model-server) and set `CWM_TEMPLATE_SERVER=http://127.0.0.1:8080` in the environment. Without that variable the local Transformers checks still run.

```sh
CWM_MODEL_PATH=/path/to/MiniCPM5-1B HF_HUB_OFFLINE=1 python -m unittest -v test_template
```

The stock generation prefix with thinking disabled ends in `<|im_start|>assistant\n<think>\n\n</think>\n\n` (newlines shown as escapes). Rendering a completed assistant message with no reasoning omits the empty thinking block. Training uses the inference prefix followed by the target IDs and turn end. On the tested CSV, compact JSON, and unindented TypeScript answers this equals encoding the whole string. A target beginning with a newline can merge with the prefix's final newlines under BPE. The tests check the shifted label positions used for training.

Under Transformers the stock template renders two assistant calls as ordered XML with CDATA for a multiline string containing `<` and `&`. It places consecutive tool results in separate `<tool_response>` elements of one user turn. It inserts string observations verbatim. Literal `</s>` and `<|im_end|>` in a quoted JSON string still encode to 1 and 130073. For project observation and action JSON, escape literal `<` and `/` in the serialized text as `\u003c` and `\u002f` before tokenization. JSON decoding restores the original Unicode text, line breaks and literal backslashes. Apply the same encoding in training and serving.

The b6602 Q8 server matched Transformers' rendered text and token IDs for an ordinary exchange and a follow-up, including multiline Unicode, XML and literal control-token spellings. Its native `tools` request returned HTTP 500 on the release template's `tojson(ensure_ascii=False)` call. The ordinary JSON-in-message protocol works on that build.

On the loaded FP32 model the input embedding and output head have separate storage. Each of the 16 query heads and two KV heads has dimension 128. A forced-token generation check exercises both EOS IDs, including the shared padding ID 1. Real tokens with ID 1 in the input remain attended, while positions added for batch padding have mask zero.

## Use the same adapter with llama.cpp

Pass the checked-in FP32 adapter alongside a GGUF of the **openbmb/MiniCPM5-1B post-trained release**. Keep the runtime's base GGUF in its ordinary cache.

```sh
llama-server -m /path/to/MiniCPM5-1B.gguf --lora ./cwm-minicpm5-lora-f32.gguf
```

Recreate the export using the official converter revision from this run. `CWM_MODEL_PATH` must point to the pinned Hugging Face snapshot for this command.

```sh
git clone https://github.com/ggml-org/llama.cpp.git /tmp/mini-llama-cpp
git -C /tmp/mini-llama-cpp checkout a300a9c33462f23d9d61e951650d249486f2b0f6
python /tmp/mini-llama-cpp/convert_lora_to_gguf.py --base "$CWM_MODEL_PATH" --outtype f32 \
  --outfile /tmp/cwm-minicpm5-lora-f32.gguf adapter
cmp cwm-minicpm5-lora-f32.gguf /tmp/cwm-minicpm5-lora-f32.gguf
```

The converter wrote two tensors, `blk.23.ffn_down.weight.lora_a` and `lora_b`, and alpha 8. All 49,152 FP32 values matched the PEFT tensors bit-for-bit. GGUF SHA-256 is `496ad6e4329e585283b5f33b41117deae5fae1c334691dcedcbb4ffc95672599`. The score table measures Transformers FP32 inference. A quantized runtime can generate different text.

## Reproduce training and scoring

The [frozen protocol](protocol.md) defines the task before training. The training inputs are the 48 earlier [V8 oracle traces](../recurrent/data/fixed.jsonl.gz) on eight programs. Each of their 98 adjacent function-pause pairs supplies a source, current observation, resume action and target. The filename and function name are fixed within a query. The encoder checks for one stack frame and exactly two integer locals. `args`, the remainder of the trace, final outcome, successor candidates and family identifier are unavailable to generation. The benchmark is conditional on a next function pause existing and excludes module and terminal transitions.

The trainable matrices modify layer 23's MLP down projection, with 49,152 trainable parameters out of a 1,080,632,832-parameter checkpoint. Cache the input to that projection and the unmodified layer's final residual for each target position. During fitting, apply the low-rank change to that residual and pass it through the original final RMS norm and unembedding. These are the same logits as running the adapted final block directly, which the trainer checks before saving. Use full-vocabulary cross-entropy on 1,076 target token positions including turn ends. With seed 17, draw batches of 32 positions for 160 AdamW updates. No model selection uses the held programs. The PEFT safetensors SHA-256 is `3609718b30c2bdd25cf1c244d95e79d5a0125fe07a8913a215f54c37b66dfa98`.

```sh
python train.py --out /tmp/fresh-mini-adapter
python score.py held.jsonl.gz --adapter /tmp/fresh-mini-adapter > /tmp/mini-scores.json
python -c 'import json; d=json.load(open("/tmp/mini-scores.json")); print({k:(d[k]["counts"],d[k]["nll"]) for k in ("base","adapted")})'
python -m unittest test_integrity
```

The scorer runs both models on identical source-disjoint queries. Both use the model's chat template with thinking disabled, a maximum of 32 new tokens, and the full vocabulary. Exact match uses the complete decoded response after stripping surrounding whitespace. The `valid` count checks only CSV structure and the numeric domain. The `inside_source` diagnostic additionally requires the coordinate to name a UTF-16 code unit in the supplied source. Breakpoint reachability requires a separate test. Rows outside the CSV or numeric domain earn zero for field accuracy. Token NLL scores the true row and end token conditioned on their true prefix. [Recorded scores](scores.json.gz) include every generated string, target, current row, source digest and count.

Before fitting or scoring, the official entry points verify the SHA-256 of the complete uncompressed training tape (`96c458b2c043df456f0db53129d51beaedfed0b5c6164f5d6a2039b87d9972fb`). Scoring also requires the exact held tape (`98c719f0deccac27a242ee5ad52c0ab924d15895512cb877b2632bf7017024c7`). These digests cover every byte of source, frame, outcome and record order. The [training corpus revision](https://github.com/ethan-wickstrom/experiments/commit/bdca8db4ebc4cda7b5dd1cb64378eb8f23876db0) and [frozen held-source manifest](https://github.com/ethan-wickstrom/experiments/commit/1044b99) identify their origin. Fitting and scoring verify any local base snapshot against the release digests. The score report identifies the exact adapter weights and config used, including when a separately reproduced adapter is supplied. Grading and frame projection require safe integers, positive coordinates and canonical decimal output spelling. Malformed rows receive zero partial credit even if their site or locals match.

To regenerate the fresh traces, install the CWM dependencies as described in the [project README](../../README.md), then run the following with Bun 1.4.4 and Node 24.19.0 on PATH:

```sh
bun collect.ts /tmp/fresh-mini-held.jsonl
gzip -dc held.jsonl.gz | cmp - /tmp/fresh-mini-held.jsonl
```
