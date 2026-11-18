# Ranking two proposed TypeScript edits

Keep the [C2 source generator](../c2/README.md) loaded in the acting host. It produces complete replacement files using the directed C2 prompt. Submit two writes for the same path to this separate CPU ranker. A positive preference predicts which write better matches the visible goal and tests. The host can then apply a write and run checks. The ranker performs inference on text and has no file execution or oracle backend.

## Run

Use the [pinned MiniCPM5 CPU environment](../README.md#reproduction). From the repository root, start one persistent process.

```sh
export CWM_MODEL_PATH=/path/to/verified/MiniCPM5-1B
python cwm/bench/development/ranking/rank.py --serve --arm C2
```

Send one UTF-8 JSON object per line. All file texts include their actual newlines, escaped according to ordinary JSON. The path is host-selected. Supply the files currently visible to the policy, including the visible tests. For example:

```json
{
  "goal": "Return the last element.",
  "path": "item.ts",
  "files": [
    { "path": "item.ts", "text": "export const item = (xs: number[]) => xs[1];\n" },
    {
      "path": "item.test.ts",
      "text": "import {expect,test} from 'bun:test'; import {item} from './item'; test('end',()=>expect(item([3,7,9])).toBe(9));\n"
    }
  ],
  "candidates": [
    { "op": "write", "path": "item.ts", "text": "export const item = (xs: number[]) => xs[0];\n" },
    {
      "op": "write",
      "path": "item.ts",
      "text": "export const item = (xs: number[]) => xs.at(-1);\n"
    }
  ]
}
```

Each result contains two centered relative scores in input order and a zero-based choice. A margin of at most 1e-8 in absolute value returns a null choice. Scores are preferences in this pair, without probability calibration. The service rejects an over-budget full input with an error object. The default is 4,096 tokens per rendered prompt, adjustable with --max-tokens up to the base context limit. For a single request, omit --serve. Use --arm A or --arm B2 for the same trained-head design on the release model or policy-only adapter. Adding --method comparison uses only that model's untrained order-corrected A/B judgment.

## Supervision and model

The [frozen protocol](protocol.md) predates extraction and scores. The 10 original training families provide 30 reversal blocks. Each block supplies two competing writes and two requirements. Within each requirement, the candidates share the exact same visible state. The current starting file and candidate bytes also stay fixed across the reversal, while the user goal and visible test change. Across the two requirements each candidate passed one real Bun run and failed the other. Extract only the observed binary preference as supervision. A candidate-only scorer necessarily gets at most one fork in each block.

A, B2 and C2 share all backbone parameters through the input of the final MLP down projection. For a new prompt, one CPU base forward yields its residual and MLP input. Add the frozen arm's low-rank update and apply the release final normalization. The live-equivalence test compares these states and margins to standard PEFT forwards. The archived-history diagnostic uses the existing C2 cached tensors at the last prompt token, before any observed target or stop token enters the input. Historical forecasts include earlier observations. The order-only comparison holds current inputs and instruction constant and changes only the JSON field order.

The learned readout uses a candidate-first JSON prompt containing the full write, current goal, selected path and visible files. It takes the difference between candidates for each feature group:

- The hidden state at the final prompt token and the mean hidden state over the visible goal.
- Mean causal log probability of tokens inside the escaped goal and visible test texts. Each token is scored from its predecessor. Only complete token offsets inside those fields count. Files in test directories or with a .test. or .spec. component in the filename contribute to test likelihood. Other supplied files still enter the full context.
- The pass-minus-fail first-token margin.
- A direct A/B judgment with both candidates in the same input. Score A minus B in both presentations and take half their difference to cancel position preference.

Let d be the difference vector scaled by each feature group's training-fold RMS length and y be +1 when the first candidate passed, -1 otherwise. For each fork set m = y wᵀd. Fit w using equal weights for mean softplus(-m) across requests and mean softplus(-(m₀+m₁)/2) across reversal blocks, plus 0.05 times the squared weight norm. Each fork still incurs its own loss when its choice is wrong. The optimizer starts at zero and runs full-batch FP64 L-BFGS with fixed settings. The head has 3,076 coefficients. Saved coefficients absorb the training scales. Swapping writes negates the feature differences and exchanges their scores.

## Reproduce

Run from this directory. The shipped feature cache contains pair differences for the 60 requests. Refitting only the heads needs the pinned Python packages and the checked-in training tapes.

```sh
work=$(mktemp -d)
gzip -dc features.pt.gz > "$work/ranker-features.pt"
python train.py "$work/ranker-features.pt" "$work/heads"
for arm in A B2 C2; do
  cmp "weights/$arm.safetensors" "$work/heads/$arm.safetensors"
done
cmp weights/fold-predictions.jsonl.gz "$work/heads/fold-predictions.jsonl.gz"
```

To rebuild features on the pinned eight-thread CPU environment, use the original C2 cache or recreate it. The builder verifies the complete oracle, derived training rows and each original input, residual and label tensor before extracting paired differences. New prompt features use FP32. Cache archive byte identity depends on PyTorch, CPU numerics and basename. The released compressed cache preserves the exact fitting inputs.

```sh
export CWM_THREADS=8
python ../c2/cache.py "$work/c2-features.pt"
mkdir "$work/rebuild"
python build.py "$work/c2-features.pt" "$work/rebuild/ranker-features.pt"
sha256sum "$work/rebuild/ranker-features.pt"
python -m unittest -v test_rank
```

## Frozen diagnostics

Each cell below gives **correct requests out of 60 / complete reversals out of 30**. Each fitted head predicted all six requests for a family after training on the other nine. Every arm and method had zero ties. Direct model margins and visible-token likelihoods use no trained head.

| Readout                                                | Unchanged A | Policy-only B2 | Joint C2    |
| ------------------------------------------------------ | ----------- | -------------- | ----------- |
| Native forecast margin, archived history               | 36 / 8      | 35 / 6         | 37 / 8      |
| Learned archived final state                           | 39 / 9      | 39 / 9         | 39 / 9      |
| Learned candidate-last final state, current state only | 39 / 9      | 39 / 9         | 39 / 9      |
| Learned candidate-first final state, same information  | 35 / 6      | 34 / 5         | 35 / 6      |
| Direct order-corrected A/B judgment                    | 37 / 7      | 37 / 7         | 36 / 6      |
| Candidate-first goal likelihood alone                  | 43 / 14     | 45 / 16        | 47 / 18     |
| Candidate-first fitted goal and test likelihoods       | 46 / 17     | 45 / 16        | 47 / 17     |
| **Released head design**                               | **45 / 16** | **45 / 17**    | **44 / 15** |

The C2 head improved on its native archived margin by seven correct requests and seven complete reversals. Its request count improved on seven families and tied on three. Putting the edit first reduced held-family separability at the final prompt token. Reading likelihoods **at the requirement tokens** recovered conditional information. The predeclared combined C2 head scored below the simpler requirement-likelihood diagnostic. The matched A and B2 heads also scored slightly higher than the combined C2 head. These data support improved candidate ranking under this readout and provide no evidence that joint execution training caused the gain.

The full C2 head refit on all 30 blocks gets 45 requests and 16 complete reversals on those same blocks. The 44/60 and 15/30 figures above come from out-of-fold heads. The released C2 and B2 backbones had already seen every family during prior LoRA training. Only A provides family-held-out readout diagnostics with an experiment-unadapted backbone. Two candidates from trusted authored alternatives are easier to evaluate than arbitrary generated writes. Neither the parent project's independent reversal suite nor its coding suite enters this experiment.

The metrics, per-fork margins, model and tensor provenance are under `weights/`. The following command starts fresh A, B2 and C2 processes through the persistent public CLI. It checks score agreement with the frozen features, swapped scores, ties on identical writes, and recovery from invalid requests.

```sh
python check_release.py "$work/ranker-features.pt"
```
