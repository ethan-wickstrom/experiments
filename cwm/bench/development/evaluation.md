# Project evaluation protocol

The independently authored fixture commit dc9d3ae contains three project lineages and two ordered requests per lineage. Run the same quantized base and CPU serving configuration with no adapter (A), coding-only (B), and joint (C). Each starts with the original project files and an empty history. No demonstrations, reference edits, test outcomes, or hidden checks are supplied. The two turns share a working tree and transcript, even when the first fails. Score a follow-up only if all independent checks through that turn pass in fresh containers.

Give each turn eight greedy policy decisions with at most 768 generated tokens per decision. Use the stock no-thinking chat template and the same action grammar for every arm. The grammar can select a still-unread path, replace or create a source, test a changed snapshot, or finish. Observations remain in context. Repeating a read or unchanged test supplies no new information and is excluded from decoding. All models can stop or exhaust the budget. A model finish signal alone earns no task credit.

In a separate prospective paired decision test, disclose the goal, current files and one candidate replacement. Record a direct endorsement and a downstream test forecast before running the test in a disposable copy. Each selector has one greedy eight-token call per candidate, with identical file and edit context. Count a selection only for a unique positive and remaining negative answers. Report ties, invalid outputs and token use. The outcome is passing the visible suite. Independent task acceptance and development forecast scores have separate denominators. Six alternatives on three projects cannot establish general transfer.

## Live results

The frozen blind full-context decision run disclosed all visible file bytes on the opening `unread` decision. All 60 training decisions at that status disclosed an empty file list. Initial `done` choices on that run therefore measure behavior under a changed observation contract. Direct source generation used the complete visible project in training and evaluation.

All three arms failed both the initial request and the cumulative follow-up on each free-action project (offline task board, Unicode editor and asynchronous sample reader). All three also failed both requests on each directed project (invoice totals and delimited export). The cumulative graders ran 9 individual checks per arm for policy and 6 for directed editing. Every grader ran and failed. Each transcript includes the final source and separate raw test output. [Transcripts](results)

| Arm | Free-action turns accepted | Generated decisions | Writes applied | Actual tests in policy | Budget exits | Input / output tokens | Directed turns accepted | Directed calls | Directed input / output |
| --- | -------------------------: | ------------------: | -------------: | ---------------------: | -----------: | --------------------: | ----------------------: | -------------: | ----------------------: |
| A   |                        0/6 |                  43 |             22 |                      0 |            4 |        39,199 / 3,129 |                     0/4 |              6 |             1,979 / 570 |
| B   |                        0/6 |                  15 |              0 |                      6 |            0 |           3,899 / 107 |                     0/4 |              6 |             1,750 / 464 |
| C   |                        0/6 |                  14 |              0 |                      5 |            0 |           3,370 / 100 |                     0/4 |              5 |           1,554 / 1,282 |

A also attempted five rejected writes. B and C used valid actions and stopped with `done` on all six turns, including after failed tests. Direct editing gave the user-selected file and up to two 768-token proposals per request with actual test feedback. A and B each wrote four times, reached the two-attempt budget twice and produced an invalid edit twice. C applied one write and ended three turns with invalid output and one with a capped generation. Policy wall times summed to 225.24, 124.20 and 11.72 seconds respectively. Directed times were 35.28, 383.15 and 72.07 seconds. Collection overlapped with other CPU work, so these are interaction records rather than comparative speed measurements.

On the three original choice pairs, all arms endorsed both alternatives in every pair. A and C each forecast 3/6 words correctly and tied on all three pairs. B produced five out-of-domain words and one incorrect prediction, leaving all three pairs unresolved. Each selector consumed 3,065 input and 12 output tokens per arm over the six calls. A second probe added a preread violation and a test forecast after each accepted write. On six actual rejections, six passes and six failures, A was correct on 6/18, B on 0/18 (16 invalid), C on 6/18 and C2 on 7/18. None correctly anticipated an unread replacement being rejected.

The six specification reversals have two conflicting requirements per family and two byte-identical alternatives across requirements. Actual Bun results give one passing alternative per pair. A, B and C each ranked the passing edit higher for 7/12 requirements with the pass-minus-fail logit and 8/12 with direct endorsement (yes-minus-no). They chose correctly on both opposite requirements in only 1/6 and 2/6 families respectively. C2 scored 8/12 and 2/6 with either signal. Preference and forecast consume one forward pass per candidate. The changes in token margins did little to change decisions. [Fixtures](reversals.ts) · [Raw logits and observations](results/reversals.json.gz)

Across five fresh TypeScript execution boundaries, full and reconstructible-delta predictions were each 0/5 exact for every original arm. In each format A had four capped generations and one invalid result. B and C each had four wrong full observations and one invalid full observation. For delta each had four invalid and one capped response. All cases had oracle coverage and every endpoint returned. C's smaller token loss on the separate scalar retention set also yielded 0/6 exact self-fed rollouts. [Transfer tasks and scoring](transfer.ts) · [Scalar retention](README.md#fresh-execution-and-retention)

The second training comparison increased the final-layer rank to 32, trained on raw file and decision tokens, and balanced opposing write forecasts. Its independently frozen project evaluation separates action selection and raw source generation. [Training and checkpoints](c2/README.md) · [Blind comparison](c2-results/README.md)

## Learned ranking and proposal coverage

On the six paired reversal families, the [A head](results/rank-A.json.gz) ranked the passing candidate first on 9/12 requests and both forks of 3/6 families. [B2](results/rank-B2.json.gz) and [C2](results/rank-C2.json.gz) each ranked 8/12 requests and both forks of 2/6 families correctly. On three original project pairs, A scored 1/3, B2 and C2 each scored 0/3. All 45 choices agreed after swapping the candidate order. Each pair had one actual Bun pass and one failure.

On the original six cumulative requests C2 produced seven complete parseable files in twelve attempts. None passed all the independent checks for its turn. On five turns only one proposal survived parsing and stop validation. On the remaining turn both candidates failed. Ranking could not have yielded a passing edit from these samples. The function-body experiment also solved 0/6 across each of its three arms. [Full-file proposals and individual grades](results/plan-C2.json.gz) · [Body-level observations and costs](body-results/README.md)

## Independent diagnostics for the line editor

Freeze two diagnostics before loading either trained line-editor checkpoint. Score the original 24 candidate forecasts, ten individual V8 pauses and four self-fed rollouts on the exact same weights used for editing. Separately, for each of the 24 local held requests, add two comment lines either before or after its module. This moves the required span by two lines while preserving both candidate coordinates, the requested behavior and the other model inputs. Score the joint token log probability of each complete coordinate string and its native stop under each layout. Both locations are legal in both versions. A pair succeeds only if the model's preference reverses in the correct direction. Each family contributes six requests. This measures a forced choice between two spans. The independent external evaluator measures unconstrained location choice and actual behavior. [Consequence and rollout scoring](local_edit/world_score.py) · [Location intervention](local_edit/position_score.py)

A retrospective debugger check groups real transitions with the same current pause, two distinct source programs and different oracle successors. Two such pairs occur in the frozen ten transitions. In both pairs the joint editor greedily returned the same next row under either program. With both actual successors supplied as alternatives for teacher-forced scoring, neither the base nor the joint editor reversed its preference correctly on either pair. The source and current row are the only model inputs. Scores include every target token and the native stop. [Scorer](local_edit/source_pairs.py) · [Base](results/source-pairs-base.json.gz) · [Joint](results/source-pairs-trained.json.gz)

## Reproduce

Build the sandbox from the project root as in the [project guide](../../PROMPTING.md#work-on-a-project). From this benchmark directory, start one b6602 server per arm in turn. Set `BASE_GGUF` to the pinned Q8_0 and `ARM` to A, B or C. Use a fresh result directory for each run.

```bash
lora=()
if [[ "$ARM" != A ]]; then lora=(--lora "$ARM/adapter-f32.gguf"); fi
llama-server -m "$BASE_GGUF" "${lora[@]}" --alias project-eval --jinja \
  -c 16384 --parallel 1 -t 4 -tb 4 --host 127.0.0.1 --port 8082
```

```bash
url=http://127.0.0.1:8082/v1/chat/completions
out=$(mktemp -d)
bun projects-evaluate.ts "$url" project-eval "$out/policy.json.gz" policy
bun projects-evaluate.ts "$url" project-eval "$out/directed.json.gz" directed
bun action-consequences.ts "$url" project-eval "$out/boundary.json.gz"
bun transfer.ts "$url" project-eval "$out/transfer.json"
# With CWM_MODEL_PATH and CWM_PYTHON from the pinned training setup
for arm in A B2 C2; do bun rank-evaluate.ts "$arm" "$out/rank-$arm.json.gz"; done
# Point url and alias at the F16 C2 server for the proposal run.
bun plan-evaluate.ts "$url" project-eval "$out/plan.json.gz"
# With the verified FP32 snapshot and Python environment from the training guide
bun reversals.ts "$out/reversals.json.gz"
bun reversals.ts "$out/reversals-2.json.gz" B2 C2
for arm in base trained edit-only; do
  "$CWM_PYTHON" local_edit/world_score.py "$arm" "$out/world-$arm.json.gz"
  "$CWM_PYTHON" local_edit/position_score.py "$arm" "$out/position-$arm.json.gz"
  "$CWM_PYTHON" local_edit/source_pairs.py "$arm" "$out/source-pairs-$arm.json.gz"
done
```
