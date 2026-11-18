# MiniCPM5 for TypeScript project actions and consequences

A is the unchanged [MiniCPM5-1B post-trained release](https://huggingface.co/openbmb/MiniCPM5-1B/tree/ac83f813ba7da263c51a9f3ec37c2072597e54af). B and C are independently trained derivatives of A. B learned from coding actions on six libraries. C shared its adapter between coding actions, Bun test forecasts and V8 pause forecasts. [Base and derivative fingerprints](artifacts.json) · [Frozen training protocol](protocol.md)

## Fresh execution and retention

Three unseen scalar programs produced 23 next-pause transitions across six invocations. C assigned more probability to the observed next tokens, but every arm missed every complete pause and every complete rollout.

| Metric                                     | A release | B coding | C joint |
| ------------------------------------------ | --------: | -------: | ------: |
| Exact next pause                           |      0/23 |     0/23 |    0/23 |
| Within CSV and numeric domain              |      0/23 |     0/23 |   20/23 |
| Within domain and coordinate inside source |      0/23 |     0/23 |    4/23 |
| Correct event, line and column             |      0/23 |     0/23 |    1/23 |
| Both locals correct                        |      0/23 |     0/23 |    3/23 |
| Both locals correct on changes             |      0/12 |     0/12 |    1/12 |
| Target-token NLL, nats (242 tokens)        |   1.34854 |  1.62079 | 1.04667 |
| Exact entry-to-return rollout              |       0/6 |      0/6 |     0/6 |
| Literal short answers correct              |       0/3 |      1/3 |     1/3 |

All six rollouts diverged at the first transition in each arm. C predicted a premature return in five and produced an out-of-domain row in the sixth. Copying the current locals scores 11/23 on the locals metric. On the three free-form questions, the only exact improvement was removing quotation marks from `"caf"`. All three arms answered the comparison-type and array-length questions incorrectly. These results leave accurate execution rollouts and broad instruction retention unresolved. [A generations](data/score-A.json.gz) · [B generations](data/score-B.json.gz) · [C generations](data/score-C.json.gz)

## Use the weights

Pass **one** adapter to a server running a GGUF of that exact base. Run plain `llama-server -m "$BASE_GGUF"` for A. B and C have one FP32 GGUF each, around 385 KiB, with two tensors checked coefficient-by-coefficient against their respective PEFT weights.

```sh
# From cwm/bench/development
llama-server -m "$BASE_GGUF" --lora B/adapter-f32.gguf
# Or start arm C
llama-server -m "$BASE_GGUF" --lora C/adapter-f32.gguf
```

For direct Transformers inference, activate the environment described below. This command sends one ordinary user message under the release chat template with thinking disabled. Substitute `B/peft` or `--base` to select the other arms.

```sh
python ../minicpm/prompt.py --adapter C/peft --text 'Choose one TypeScript project action as compact JSON. Actions: read(path), write(path,text), test(), done(). Use the key op for the action name. Read before replacing a file. Run tests after changes.
{"files":["checks.test.ts","numbers.ts"],"history":[{"user":"Round each number down to an integer."}]}' --max-new-tokens 96
```

[The wire contract](contract.ts) serializes the sorted filenames and complete observed history as compact JSON. A forecast appends the specific candidate action. The runtime supplies the corresponding instruction. An independent `--source ... --current ...` request to the same adapter uses the original next-pause prompt. The live project evaluation uses schema-constrained actions for all three arms and free word forecasts. The retention results here use unconstrained, greedy FP32 decoding.

## Training evidence

| Task             | Records | Supervised tokens including stops | Prompt tokens, min / median / max | Answer tokens, min / median / max |
| ---------------- | ------: | --------------------------------: | --------------------------------- | --------------------------------- |
| Coding policy    |      66 |                             1,002 | 83 / 281 / 486                    | 6 / 6 / 57                        |
| Project forecast |      66 |                               138 | 93 / 258 / 459                    | 2 / 2 / 3                         |
| V8 next pause    |      98 |                             1,076 | 95 / 103 / 105                    | 10 / 10 / 12                      |

The Bun collector executed the authored duration, initials, basket total, color palette, filename extension and arithmetic mean projects. Each had an initial feature request and a follow-up request with an expanded regression test supplied by the user. Both requests ended with a verified passing test. Reads record actual bytes. Accepted writes record `written`. Tests record the exit status and a short projection of actual diagnostics. The raw tape retains stdout and stderr separately. A `done` action ends a policy turn. Its history has no tool result.

For each of 12 repair decisions, three alternatives replaced the same file from the same observed state. Each accepted candidate ran the same Bun tests, then the collector restored the original bytes. These 36 write checks produced 14 passes and 22 failures, including two imperfect alternatives that passed the available assertions. There were also 24 current-state test forecasts and six unread replacement rejections. Only demonstrated successful repair trajectories supplied policy targets. Observed failures remained visible to subsequent policy decisions. Counterfactuals supplied forecast targets only. [Cases](cases.ts) · [Collector](collect.ts) · [Raw oracle](data/oracle.jsonl.gz)

The pinned V8 training tape supplies all 98 within-function scalar transitions from 48 earlier invocations on eight programs. The TS collector owns project goals, actions and observations. The existing Python scalar projection supplies execution targets from the debugger tape. The combined [JSONL corpus](data/training.jsonl.gz) has exactly `family, task, prompt, target` on each row. The audit reconstructs every project prompt from the raw observed prefix and compares bytes. Neither a proposed edit's test result nor its hidden counterfactual siblings enter that prefix.

B and C each optimize a new rank-16, alpha-16 LoRA on layer 23's MLP down projection, with 98,304 trainable parameters. The trainer caches the original residual before final normalization and the input to the down projection at supervised positions. For features `x`, frozen residual `h` and LoRA factors `A,B`, the optimized logits are `lm_head(final_norm(h + B(A(x))))`. The trainer compares these logits with a live adapter forward pass. Tensor operations, automatic differentiation, PEFT serialization and the official GGUF converter use Python. TypeScript owns project collection, action contracts, debugger collection, and retention evaluation.

Each arm used 256 AdamW updates at 0.001, with 48 full-vocabulary loss positions per update, seed 17, eight CPU threads, FP32, no sequence truncation and no GPU. B drew 12,288 policy positions with replacement. C drew 6,144 policy, 3,072 project forecast and 3,072 execution positions. A and B did not consume forecast or execution gradients. The shared cache construction cost was paid once. The longest complete training sequence had 492 tokens. The model supervises only target token positions including the assistant stop. Full multiline observed histories stay in the input. The two adapters differ in both the objective and the amount of policy rehearsal.

The comparison tests whether supervised interaction and observation learning transfer at this scale. Training on observation-action trajectories follows [Meta CWM](https://arxiv.org/abs/2510.02387). A single acting and predicting model follows the integrated-agent question in [Qwen-AgentWorld](https://arxiv.org/abs/2606.24597). Candidate forecasts before execution and counterfactual tests from restored states draw on [ANTE](https://arxiv.org/abs/2610.15368) and [Software World Models](https://arxiv.org/abs/2610.04940). All optimization here uses supervised loss.

On the training examples, B and C both reduced policy-target NLL. The joint model obtained the lowest forecast and execution NLL. Forecast token top-1 counts were 95/138 for A, 75/138 for B and 94/138 for C. Many of these positions are answer stops. The held development evaluation measures whether a correct forecast actually helps choose edits. [Per-task training diagnostics](data/fit-diagnostics.json)

| Training target-token NLL, nats | A release | B coding | C joint |
| ------------------------------- | --------: | -------: | ------: |
| Coding policy                   |     1.519 |    0.161 |   0.221 |
| Project forecast                |     0.574 |    1.269 |   0.497 |
| Next pause                      |     1.669 |    1.995 |   0.818 |

## Reproduction

Use Bun 1.4.4 and Node 24.19.0. Install the [CWM dependencies](../../README.md) first. From this benchmark directory, install the CPU tensor environment and download the verified snapshot.

```sh
python3.11 -m venv ~/.venvs/dev-cwm
. ~/.venvs/dev-cwm/bin/activate
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.7.1
python -m pip install -r ../minicpm/requirements.txt
export CWM_MODEL_PATH="$HOME/minicpm5-release"
hf download openbmb/MiniCPM5-1B --revision ac83f813ba7da263c51a9f3ec37c2072597e54af --local-dir "$CWM_MODEL_PATH"
export CWM_PYTHON="$(command -v python)"
```

The loader stages exactly the eight digest-verified release files for local loading. The stock template, tokenizer, weights and configuration share the same pinned revision. Generation uses position masks for padding and honors both release stop IDs, 1 and 130073. A literal special-token spelling in source is retained in the stock tokenization.

```sh
work=$(mktemp -d)
bun collect.ts "$work/data"
gzip -dc data/projects.jsonl.gz | cmp - <(gzip -dc "$work/data/projects.jsonl.gz")
python corpus.py | cmp - <(gzip -dc data/training.jsonl.gz)
python -m unittest test_data test_artifacts
python features.py "$work/cache.pt"
python fit.py --arm B --cache "$work/cache.pt" --out "$work/B"
python fit.py --arm C --cache "$work/cache.pt" --out "$work/C"
cmp "$work/C/peft/adapter_model.safetensors" C/peft/adapter_model.safetensors
python diagnose.py "$work/cache.pt"
```

The shell examples use Bash process substitution. The committed raw collector transcript pins the original Bun version, exits and full output, including incidental timings. A new run reproduces the derived project rows byte-for-byte. Caching took about 162 seconds on this eight-thread CPU. The trainer periodically replaces its checkpoint atomically. It stores the LoRA matrices, AdamW moments, update count, draw generator and PyTorch random state. At update 129 it compares the uninterrupted and restored updates, including their sampled indices, loss and resulting weights. To resume in a fresh process:

```sh
python fit.py --arm C --cache "$work/cache.pt" --stop-at 128 --out "$work/half"
python fit.py --arm C --cache "$work/cache.pt" --resume "$work/half/state.pt" --out "$work/resumed"
cmp "$work/resumed/peft/adapter_model.safetensors" C/peft/adapter_model.safetensors
```

A separate fresh-process restart from update 128 reproduced the shipped C safetensors byte-for-byte. Its SHA-256 is `ee7add1d8f4427eeb8355caa6eda208998ee06dc739c6498670762ef84517e40`.

To reproduce both adapter exports using the official llama.cpp converter:

```sh
git clone https://github.com/ggml-org/llama.cpp.git "$work/llama.cpp"
git -C "$work/llama.cpp" checkout a300a9c33462f23d9d61e951650d249486f2b0f6
for arm in B C; do
  python export.py "$work/llama.cpp" "$arm/peft" "$work/$arm.gguf"
  cmp "$work/$arm.gguf" "$arm/adapter-f32.gguf"
done
```

To reproduce the post-freeze TypeScript debugger traces and the published retention comparison:

```sh
bun retention.ts "$work/retention.jsonl.gz"
gzip -dc data/retention.jsonl.gz | cmp - <(gzip -dc "$work/retention.jsonl.gz")
for arm in A B C; do
  bun evaluate.ts "$arm" > "$work/score-$arm.json"
  gzip -dc "data/score-$arm.json.gz" | cmp - "$work/score-$arm.json"
done
```

The three scalar programs and six invocations were declared before fitting. Their labels were collected after both adapter exports were committed. Each next-pause query starts at an observed frame and is conditional on another function pause. Each separate rollout starts only at the true function entry and feeds back its own successive forecasts, even after a wrong step. It stops at a predicted return, a malformed row, a repeated state, or the 16-step budget. The evaluator reports full-path equality and the length of the exactly correct prefix. The three short free-form controls score literal answer equality, so extra quotation marks count as a miss. These small controls cover only the listed scalar transitions and prompts. The independently held live coding and candidate-selection comparison is evaluated by the integration runner.
