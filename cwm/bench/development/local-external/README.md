# Independent localized TypeScript editing evaluation

Three two-turn conversations cover a photographer's contact sheets, persisted parcel pickup tickets, and a gallery's narration catalog. Each second request extends the first. Each project has two source files and cumulative visible and hidden Bun suites. The host supplies the implementation path. The model chooses both the line span and raw replacement.

## Free-location results

| Arm       | Stopped / 6 | Accepted / 6 | Changed / 6 | Exact span / eligible | Visible / 6 | Cumulative hidden / 6 | Individual hidden / 9 | Solved / 6 |
| --------- | ----------: | -----------: | ----------: | --------------------: | ----------: | --------------------: | --------------------: | ---------: |
| Base      |           2 |            0 |           0 |                   0/3 |           0 |                     0 |                     0 |          0 |
| Joint     |           3 |            3 |           3 |                   1/3 |           0 |                     0 |                     0 |          0 |
| Edit-only |           6 |            6 |           5 |                   1/3 |           1 |                     0 |                     0 |          0 |

An accepted edit stopped, reconstructed the reported source exactly and parsed as TypeScript. A solved turn also required changed source and passing visible and cumulative hidden behavior. All 18 turns produced a legal interval, including responses that hit the replacement cap. The original source matched the reference predecessor on each first turn. None of the nine policy follow-up snapshots matched its reference predecessor.

Joint and edit-only chose identical spans on all three paired first-turn inputs. Both targeted the right line in the gallery and missed the row-loop and ticket-removal lines. Joint capped on the first sheet and pickup requests and on the pickup follow-up. Edit-only produced accepted changes on those three. Both changed the sheet follow-up and first gallery turn. On the gallery follow-up joint changed the source and edit-only repeated its previous edit. The only differing interval on follow-ups was the pickup turn, where each arm saw its own previous source. Edit-only passed the first gallery visible assertion by looking up the requested language twice. Its hidden suite exercised the missing fallback.

When the reference replacement was applied at the predicted location, the three first-turn snapshots passed 0/3 for base, 1/3 for joint and 1/3 for edit-only. Both adapter passes were the gallery edit. Applying the model's already-generated replacement at the reference location passed 0/1 for base, 0/1 for joint and 0/3 for edit-only. A capped response has no completed payload for this second control. Independent strict project type checks passed all six fixed references and reported errors on two joint and four edit-only policy snapshots. These checks run after scoring.

## Seals and records

The fixture and reference preflight were committed privately at `86a7e47` before weights were available. Edit-only was added at `59b546b` before held inference. All six reference predecessors failed their new visible and hidden behaviors. All six reference fixes passed cumulative visible and hidden checks. An exact-text comparison against 204 training edit episodes and 24 trainer holdout episodes found no matching goal, implementation snapshot or test. This comparison concerns the edit datasets and does not audit base-model pretraining.

The 18-row index in `results/diagnostics/turns.jsonl` contains the goal, actual pre-edit observation, request and source digests, model span and replacement, acceptance, changed and solved flags, visible and individual hidden outcomes, hybrid eligibility and results, and query time. Its transcript paths resolve under `results/` and diagnostic paths under `results/diagnostics/`. Each compressed policy transcript includes the exact request, full visible files, raw model response, resulting source and raw Docker observations. Hybrid transcripts include the separate reference and counterfactual snapshots. `results/provenance.json` pins the editor revisions, model files, weights, environment and transcript index. Base and both adapter collections used the same inference code, verified byte-for-byte. Both adapters have 1,081,344 coefficients and matched initialization, cached features and edit draws. Joint took 256 additional optimizer updates. The small suite supports a paired description of these runs.

## Reproduction

Use the CWM dependencies and sandbox image documented in the parent development benchmark. Check out the released editor at `5579d0558153fc4f77a0817042df436c47e74358` in a separate tree. Run from this directory with the verified release snapshot and pinned Python environment. Each output directory must be fresh.

```sh
export CWM_MODEL_PATH=/path/to/minicpm5-snapshot CWM_THREADS=8 HF_HUB_OFFLINE=1
export PYTHON=/path/to/venv/bin/python TOKENIZERS_PARALLELISM=false
editor=/path/to/editor-checkout
out=$(mktemp -d)
bun preflight.ts "$out/preflight.json.gz"
for arm in base trained edit-only; do
  bun evaluate.ts "$editor" "$arm" "$out/$arm"
done
bun diagnose.ts "$out" "$out/diagnostics"
```

Wall-clock response times include the remaining process startup on each arm's first request. The release hashes, observed grades and generated source are the reproducibility checks. Raw Docker diagnostics include run-specific timings.
