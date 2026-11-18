# Predicting a changed local from source

With `x = 6` and `y = 2`, V8 paused on line 2 just before an assignment. In one program, `x = (x + y) * 2` set `x` to 16. In its paired program, `x = (x - y) * 2` set it to 8. Both resumed at the first column of line 3. The structured CWM predicted both successor frames exactly. The joint MiniCPM5 editor returned the incoming values 6 and 2 in both replies.

### Six fresh source interventions

Three pairs of programs change operator position, operand order or assignment destination. Each pair runs twice with different inputs. Within each pair the complete current frame and next pause location are identical, and the assignments change different values. A predictor that ignores the source can get at most one complete frame per pair. The preflight checks all six source strings against the execution training tape. The first manifest had one training-source collision, which was replaced before model inference. [Protocol](protocol.md) · [V8 observations](tape.jsonl.gz)

| Predictor                                      | Legal rows / 12 | Correct next site and event / 12 | Correct changed locals / 12 | Exact next frame / 12 | Both frames exact / 6 pairs |
| ---------------------------------------------- | --------------: | -------------------------------: | --------------------------: | --------------------: | --------------------------: |
| [Base MiniCPM5](results/base.json.gz)          |               0 |                                0 |                           0 |                     0 |                           0 |
| [Edit-only adapter](results/edit-only.json.gz) |               0 |                                0 |                           0 |                     0 |                           0 |
| [Joint adapter](results/trained.json.gz)       |              11 |                               11 |                           0 |                     0 |                           0 |
| [Structured CWM](results/structured.json.gz)   |              12 |                               12 |                          12 |                    12 |                           6 |

The structured predictor was fitted on the 48 invocations that supply the joint adapter's execution training rows. It receives a parsed control-flow graph, learns operator rules from observed operand/result triples, and composes those rules at inference. The joint adapter receives source text and predicts tokens. It emitted the two incoming local values in the local-value positions on all 12 trials, including one malformed row. The base and edit-only models are controls without these execution updates. The six pairs cover integer arithmetic on two scalar bindings. They do not measure general project execution or editing success.

### Original four debugger runs

The frozen original probe has ten adjacent function pauses, four assignments that change locals, and four full trajectories. Using the original tape, the same structured fit predicted all four local changes, 9/10 full successor frames, both same-current-state pairs, and 3/4 self-fed trajectories. Its one wrong frame followed `y = x + y` in the else branch. It produced the correct updated `y = 4` and returned 4, one pause before V8's return event. The joint adapter produced 1/10 full successors and 0/4 self-fed trajectories. The original comparison is retrospective. [Structured predictions](results/structured-original.json.gz) · [Adapter scores](../evaluation.md#independent-diagnostics-for-the-line-editor)

### Reproduce

From `cwm/`, use Bun 1.4.4, Node 24.19.0 and the [pinned MiniCPM environment](../README.md#reproduction). The commands below use Bash. The first comparison recollects the oracle tape. The others fit the structured predictor or load the released weights and compare complete reports.

```bash
set -eo pipefail
d=bench/development/interventions
python "$d/programs.py" | bun cwm.ts | cmp - <(gzip -dc "$d/tape.jsonl.gz")
export CWM_MODEL_PATH=/path/to/pinned/MiniCPM5-1B
export CWM_THREADS=4 OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false
for arm in structured base trained edit-only; do
  python "$d/evaluate_interventions.py" "$arm" | cmp - <(gzip -dc "$d/results/$arm.json.gz")
done
python "$d/evaluate_interventions.py" structured --original | cmp - <(gzip -dc "$d/results/structured-original.json.gz")
```
