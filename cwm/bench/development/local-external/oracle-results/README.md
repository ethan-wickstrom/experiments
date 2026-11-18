# Reference-span FILL results

Supplying the correct location yielded **0/6 solved turns** for both checkpoints. Neither produced an exact reference replacement or passed the hidden suite for the current request.

| Arm       | Stopped / 6 | Accepted / 6 | Changed / 6 | Visible / 6 | Cumulative hidden / 6 | Individual hidden / 9 |
| --------- | ----------: | -----------: | ----------: | ----------: | --------------------: | --------------------: |
| Joint     |           3 |            3 |           2 |           0 |                     0 |                     2 |
| Edit-only |           6 |            5 |           4 |           1 |                     0 |                     1 |

The individual hidden passes were earlier behaviors on follow-ups. Joint hit the cap on the first sheet request and both parcel requests. Both arms repeated the canonical predecessor's existing implementation for the gallery follow-up. Edit-only passed the first gallery visible test and missed its hidden fallback case. Its first sheet response replaced a loop opening with an early return and left the file syntactically invalid. In the first gallery request each arm received exactly the same FILL prompt as in its free-location run and reproduced its earlier reply.

## Provenance

All 12 generations used the released `Editor.generate` and `wire.user` at `5579d0558153fc4f77a0817042df436c47e74358`, with the same verified base and adapter hashes, greedy decoding, 96 replacement tokens, eight CPU threads, and Python environment recorded in `../results/provenance.json`. The prospective scores are frozen at `4eff66289d211dbf109d5cc2b5337f18fa51e697`. This later diagnostic uses canonical follow-up sources containing the validated prior reference edit. It measures replacement generation with supplied locations on that reference trajectory.

The intervals below are zero-based, end-exclusive LF line bounds derived from the independently authored reference edits sealed at `86a7e47054b0baa71ba1e58265b626e69e18356b`. Each interval was checked against the corresponding predecessor and reference in the preflight artifact with gzip SHA-256 `fda0cb2f1968a899bf336a22d2093d83a1f04f6670dab603f5d54f2a9109f057`.

| Project       | First request | Follow-up |
| ------------- | ------------: | --------: |
| Contact sheet |        [5, 6) |    [6, 7) |
| Parcel locker |        [6, 7) |    [4, 5) |
| Gallery audio |        [3, 4) |    [3, 4) |

Each arm's `turns.jsonl` lists its six transcripts, source and compressed transcript digests, reference span, stop status, source changes, exact replacement agreement, timings and behavioral grades. Each compressed transcript includes the actual pre-edit run, visible request, exact FILL prompt, raw response, applied source and separate executed suites. The prompts were independently reconstructed and checked against the released formatter on the sealed source, goal, files, diagnostics and numeric interval.

To reproduce from the parent benchmark directory, use the environment and checkout in the prospective reproduction instructions and choose fresh output directories.

```sh
for arm in trained edit-only; do
  bun oracle.ts "$editor" "$arm" "$out/oracle-$arm"
done
```
