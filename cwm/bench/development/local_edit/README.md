# MiniCPM5 localized TypeScript edits

Given a goal and a host-selected file, the model first chooses a contiguous span and then generates its replacement. The host applies the splice to exactly the supplied snapshot. Tests remain observations produced by Bun. The model also trains on real test outcomes and V8 pauses.

## Use the editor

Use the [pinned Python and CPU model setup](../README.md#reproduction). Run from the repository root. Requests and responses are one UTF-8 JSON object per line. The same interface supports the unchanged base, the joint trained adapter and the edit-only control.

```sh
export CWM_MODEL_PATH=/path/to/verified/MiniCPM5-1B
python cwm/bench/development/local_edit/edit.py --serve --arm trained
```

For a single request, omit --serve and provide this input on stdin. Include all currently visible project sources and tests. The optional observed string can carry actual pre-edit test feedback.

```json
{
  "goal": "Set the exported name to \"primary\".",
  "path": "color.ts",
  "files": [
    { "path": "color.ts", "text": "// default palette\nexport const name = \"main\";\n" },
    {
      "path": "checks.test.ts",
      "text": "import {expect,test} from 'bun:test'; import {name} from './color'; test('name',()=>expect(name).toBe('primary'));\n"
    }
  ]
}
```

A completed response supplies stopped, start, end, replacement and text. Line boundaries are zero-based, start-inclusive and end-exclusive. Each line includes its terminating LF when present. CR bytes remain part of the line, a final partial line counts, and a trailing LF creates no extra line. An empty range inserts text. An empty replacement deletes the selected range. The host copies the exact strings before and after the range. Tests may still fail after a model-confirmed stop. A decoding cap returns stopped=false and an error. The default budget is 96 new replacement tokens with a 4,096-token input limit per prompt. No stage retrieves extra files, executes candidate code or rewrites whitespace. To compare arms, substitute --arm base or --arm edit-only.

The locator receives the goal, selected path, numbered current lines, other visible files and optional observed feedback. Both calls use one stock user message, reversible C2-style JSON escapes, the release template with thinking disabled, and the exact inference generation prefix. The locator greedily decodes decimal start:end under a grammar covering all legal spans. The replacement call adds only the model-selected span. Its output is raw, including indentation and the final newline when generated. Both release stop IDs count.

## Data and training

The [protocol](protocol.md) fixes the data, depth and final update before held-family scoring. Twelve new training libraries supply 144 actual before/fail and after/pass transitions, including insertions, deletions, multiline replacements and CRLF. Each library has a behavior edit and two setting edits, with both directions and two source layouts. Four separate local families provide 24 evaluation requests with one layout and additional assertions. These families share the setting-edit design with training and have different functions and requirements.

Add the 60 verified C2 edits to reach 204 distinct training before/after examples. Remove the longest identical prefix and suffix of complete lines to derive the single minimum covering line range for each pair. Verify applying each splice reconstructs all after bytes. The two stages provide 204 location targets and 204 raw replacements. The joint arm also receives 140 frozen project forecast rows and 98 native next-pause rows. Only the actual pre-edit feedback is eligible to enter edit prompts. The post-edit exit, hidden assertions and accepted after source stay outside model inputs.

Cache exact FP32 activations entering layer 22 and train LoRA on five projections in each of the two remaining blocks. The trainable query, key, value and attention output projections change how the model combines positions, and the MLP down projections change its token features. Both blocks use their full causal attention mask and original rotary positions. Compare cache replay and standard complete-forward logits for one example of every task before and after fitting. The [CPU timing](data/timing.json) reports six measured updates per depth. The two-block median after warm-up was 0.152 seconds on the 177-token pilot.

The two arms use an identical seed, LoRA initialization and sequence of indexed edit draws. Training uses per-example cross entropy with location endpoint weighting. AdamW takes 2,048 updates in the joint arm and 1,792 in the control. The two arms share global-step learning rates for all 768 location and 1,024 fill steps. Only the joint arm takes 128 additional forecast updates and 128 debugger updates. An idle reserved step in the control also skips weight decay, moment evolution and the bias-correction step counter. Attribution therefore includes the additional updates.

## Reproduce

Run from this directory with the pinned CPU environment, Bun 1.4.4 and Node 24.19.0. The normalized training view is pinned, together with the original Bun tapes. A fresh collector run reproduces the sources, goals, expected checks and pre/post test exits. Raw Bun transcripts also contain temporary paths and measured durations.

```sh
export CWM_THREADS=8
work=$(mktemp -d)
python collect.py "$work/recollected"
python timing.py > "$work/timing.json"
python cache_local.py "$work/local-edit-features.pt"
for arm in trained edit-only; do
  python train_local.py "$work/local-edit-features.pt" "$work/$arm" --arm "$arm" --checkpoint "$work/$arm.pt"
done
cmp model/peft/adapter_model.safetensors "$work/trained/peft/adapter_model.safetensors"
cmp edit-only/peft/adapter_model.safetensors "$work/edit-only/peft/adapter_model.safetensors"
python -m unittest -v test_edit
bash ../c2/sandbox-image.sh
for arm in base trained edit-only; do
  CWM_THREADS=4 python score_local.py "$arm" > "$work/$arm.json"
done
```

A training checkpoint stores the optimizer, RNG, draws, count, history and all adapter tensors. Repeating the command with the same checkpoint path resumes at the next step. The released standard PEFT adapters use the original verified base weights. The inference service verifies the adapter and configuration hashes on load. During evaluation only completed patches run, each in a network-disabled, read-only non-root Bun container with resource limits. The evaluator checks the visible assertion and additional behavior independently.
