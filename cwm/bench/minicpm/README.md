# MiniCPM5 trained on TypeScript debugger pauses

A rank-eight LoRA on [openbmb/MiniCPM5-1B](https://huggingface.co/openbmb/MiniCPM5-1B/tree/ac83f813ba7da263c51a9f3ec37c2072597e54af) produced 25 well-formed forecasts and one completely correct next pause on 34 held-out transitions. The unmodified release produced zero well-formed forecasts under the same prompt. Both missed the new local values on all 12 writes.

| Fresh-source metric                 | Original weights | Trace-trained LoRA |
| ----------------------------------- | ---------------: | -----------------: |
| Complete next frame                 |             0/34 |               1/34 |
| Valid row                           |             0/34 |              25/34 |
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
printf '%s\n' 'export function run(x:number, y:number) {' 'x = x + y;' 'return x - y;' '}' > /tmp/mini-example.ts
python prompt.py --source /tmp/mini-example.ts --current 'S,2,1,2,3'
```

The loader pins the release revision shown above. The first call downloads approximately 2.16 GB of BF16 weights and loads them in FP32 for CPU inference. To use a downloaded copy, set `CWM_MODEL_PATH` to the local snapshot directory. Use `CWM_THREADS` to change the default of eight CPU threads. Both coding and pause prompts use the same PEFT weights in `adapter/`.

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
python -c 'import json; d=json.load(open("/tmp/mini-scores.json")); print({k:(v["counts"],v["nll"]) for k,v in d.items()})'
```

The scorer runs both models on identical source-disjoint queries. Both use the model's chat template with thinking disabled, a maximum of 32 new tokens, and the full vocabulary. Exact match uses the complete decoded response after stripping surrounding whitespace. Invalid rows earn zero for field accuracy. Token NLL scores the true row and end token conditioned on their true prefix. [Recorded scores](scores.json.gz) include every generated string, target, current row, source digest and count.

To regenerate the fresh traces, install the CWM dependencies as described in the [project README](../../README.md), then run the following with Bun 1.4.4 and Node 24.19.0 on PATH:

```sh
bun collect.ts /tmp/fresh-mini-held.jsonl
gzip -dc held.jsonl.gz | cmp - /tmp/fresh-mini-held.jsonl
```
