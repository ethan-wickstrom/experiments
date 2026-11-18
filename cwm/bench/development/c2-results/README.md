# Blind two-turn TypeScript project evaluation

A (released MiniCPM5-1B) and C2 each passed **0/4** cumulative requests with learned action choice and **0/4** with direct source generation on two previously unseen projects. Both policies answered `done` on the first decision four times. Direct generation also failed every initial request and follow-up. With two lineages and one greedy attempt, these observations describe this suite.

| Arm and mode                   | Cumulative passes | Visible passes | Writes accepted | Model calls | Prompt tokens | Generated tokens | Turn time, sum | Turn time, median |
| ------------------------------ | ----------------: | -------------: | --------------: | ----------: | ------------: | ---------------: | -------------: | ----------------: |
| [A policy](A-policy.json.gz)   |               0/4 |            0/4 |               0 |           4 |           937 |                8 |         6.02 s |            1.44 s |
| [C2 policy](C2-policy.json.gz) |               0/4 |            0/4 |               0 |           4 |           937 |                8 |         8.33 s |            2.10 s |
| [A source](A-source.json.gz)   |               0/4 |            0/4 |               4 |           4 |           926 |              154 |        13.12 s |            3.20 s |
| [C2 source](C2-source.json.gz) |               0/4 |            0/4 |               2 |           4 |           901 |              482 |        36.99 s |            4.89 s |

On the temperature log, both A edits still overwrote the file with one reading. C2's first reply repeated `edit` until the token cap, leaving the seed file intact. Its second returned an object without writing a file. On station departures, A returned the first qualifying clock time in input order on both turns. C2 first generated a syntax error at `Math.min(..., now)`, then wrote a function returning `null`. All six post-turn hidden suite runs failed in each mode and arm. Each gzip includes raw requests and replies, finish reasons, token use, elapsed times, actions, workspace snapshots, and isolated visible and hidden command output.

## Protocol and reproduction

The fixture was frozen at `8dd85545c0ebbf37f441d436179c67cbbe4d8be4` before either endpoint was queried. The evaluator imports `workFile` and the stock `endpoint` at `8d1812c08881131898bdb1412ac50aa8f0c963ce`. Each arm and mode starts a fresh session per project, carrying its own workspace into the follow-up. The selected source path, goal and entire visible project are disclosed. The policy receives the current status and gets eight decisions of up to eight tokens each. An edit asks the same checkpoint for up to 384 tokens of verbatim source. The ablation uses one such source call per request. Each prompt is a single stock user message, greedy, with thinking disabled. Neither mode retries. Each finished turn runs the visible suite and every hidden check through that turn in separate fresh containers. A cumulative pass requires all hidden checks due at that turn to pass with at least one executed Bun test. The later reporting fix at `436afa8` concerns a read after a write. Neither policy reached a write. Scores use executed acceptance checks.

Use Bun 1.4.4, Docker sandbox `cwm-bun-project:1.4.4` (observed image ID `sha256:b98507ea09465f02a0f6dfc3a4dab90da4c149e9cdfec463de4e780549ef33a4`), and CPU llama.cpp b6602 (`72b24d96`). The Q8_0 base SHA-256 was `0dc7638539067268774c275a14a6ec9c7e01f7eeb2cff606c8590361fa527e4c`. C2 loaded the FP32 LoRA at `b38ed45365142e7cb00e3aa8c7fa5def5c1543df`, verified SHA-256 `55a828fd72c3d1520e8d3668313c0b50dfbad48b99e8729ec251cf9ed44682cb`. A used the base alone. Both servers used `--alias blind-cwm --jinja -c 8192 --parallel 1 -t 6 -tb 6 --seed 1`. From `cwm`, run one command per arm and mode against its matching server with a fresh destination.

```sh
bun bench/development/c2-evaluate.ts "$ENDPOINT" blind-cwm "$ARM" "$MODE" "$OUT.json.gz"
```

Time covers each production turn, including any in-turn visible test. Post-turn grading and server startup are excluded. These are single-run wall times. For historical context, the original A project policy recorded 225.24 s across six turns (median 39.03 s, 43 calls, 39,199 input and 3,129 generated tokens). That policy allowed eight JSON-grammar decisions with 768 tokens each. The earlier directed A evaluation recorded 35.28 s across four turns (median 8.77 s, six calls, 1,979 input and 570 generated tokens), with up to two 768-token source attempts and a test diagnostic on retry. Both used different fixture lineages and interfaces. [Original measurements](https://github.com/ethan-wickstrom/experiments/tree/436afa8952ea96ac7cced9a842f569085f018945/cwm/bench/development/results)
