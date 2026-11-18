# Blind two-turn TypeScript project evaluation

## Training-aligned decision mode

With an empty file list at the start of each request, A, B2 and C2 each passed **0/4** cumulative requests. The change altered which actions B2 and C2 took. Only C2 reached source generation, on the station follow-up.

| Arm                              | Cumulative passes | Visible passes | Writes accepted | Model calls | Prompt tokens | Generated tokens | Turn time, sum | Turn time, median |
| -------------------------------- | ----------------: | -------------: | --------------: | ----------: | ------------: | ---------------: | -------------: | ----------------: |
| [A aligned](A-aligned.json.gz)   |               0/4 |            0/4 |               0 |           4 |           411 |                8 |         3.44 s |            0.85 s |
| [B2 aligned](B2-aligned.json.gz) |               0/4 |            0/4 |               0 |          15 |         2,017 |               30 |        10.36 s |            2.74 s |
| [C2 aligned](C2-aligned.json.gz) |               0/4 |            0/4 |               3 |          15 |         2,677 |              133 |        30.69 s |            1.28 s |

A answered `done` immediately four times. B2 tested eight times on the initial temperature request, read and tested on both follow-ups, and stopped immediately on the initial station request. C2 tested before reading and attempted an unauthorized replacement on the initial temperature request. It stopped immediately on the next two requests. On the station follow-up, C2 read the project, tested, and wrote three times. The first two replacements returned `null` and failed visible tests. The last exported `wait` in place of the required `waitMinutes`. C2 then answered `done` with a write pending verification. Post-turn grading failed the visible suite and both hidden suites.

The aligned runs use production revision `c85f426`, the same frozen thermometer and station projects, the same checkpoints and matched server settings below. In each request, an actual `read` discloses the sorted visible file bundle. The session uses those observations to authorize replacement. A test supplies its status and leaves the observed file set intact. Raw stdout and stderr stay in the event. Forecast history records C2's bounded diagnostic. The stock decision and source prompts have no diagnostic field. Each hidden suite runs on a copy after the turn ends. These are follow-up measurements on the original two lineages.

Gold-answer replay through production matched all 300 decision prompts, 60 source prompts and 140 forecast prompts from the frozen training corpus byte for byte across all 60 episodes. Replay supplies the recorded model targets and visible Bun results. The held runs instead use the live model and sandbox at every step. [Replay test](../c2/c2.test.ts)

## Historical full-context policy and direct source

A (released MiniCPM5-1B), B2, and C2 each passed **0/4** cumulative requests with learned action choice and **0/4** with direct source generation on two previously unseen projects. All three policies answered `done` on the first decision four times. Direct generation also failed every initial request and follow-up. With two lineages and one greedy attempt, these observations describe this suite.

| Arm and mode                   | Cumulative passes | Visible passes | Writes accepted | Model calls | Prompt tokens | Generated tokens | Turn time, sum | Turn time, median |
| ------------------------------ | ----------------: | -------------: | --------------: | ----------: | ------------: | ---------------: | -------------: | ----------------: |
| [A policy](A-policy.json.gz)   |               0/4 |            0/4 |               0 |           4 |           937 |                8 |         6.02 s |            1.44 s |
| [B2 policy](B2-policy.json.gz) |               0/4 |            0/4 |               0 |           4 |           937 |                8 |         7.91 s |            2.01 s |
| [C2 policy](C2-policy.json.gz) |               0/4 |            0/4 |               0 |           4 |           937 |                8 |         8.33 s |            2.10 s |
| [A source](A-source.json.gz)   |               0/4 |            0/4 |               4 |           4 |           926 |              154 |        13.12 s |            3.20 s |
| [B2 source](B2-source.json.gz) |               0/4 |            0/4 |               1 |           4 |           913 |              818 |        53.28 s |           13.11 s |
| [C2 source](C2-source.json.gz) |               0/4 |            0/4 |               2 |           4 |           901 |              482 |        36.99 s |            4.89 s |

On the temperature log, both A edits still overwrote the file with one reading. C2's first reply repeated `edit` until the token cap, leaving the seed file intact. Its second returned an object without writing a file. On station departures, A returned the first qualifying clock time in input order on both turns. C2 first generated a syntax error at `Math.min(..., now)`, then wrote a function returning `null`. B2 produced one invalid temperature function and truncated its follow-up at 384 tokens. Its first station edit referenced an undefined variable. The next reply repeated an assignment until truncation. All six post-turn hidden suite runs failed in each mode and arm. Each gzip includes raw requests and replies, finish reasons, token use, elapsed times, actions, workspace snapshots, and isolated visible and hidden command output.

## Protocol and reproduction

Use evaluator mode `aligned` for the current production policy, `full-context` for the historical policy ablation (`policy` is its original name), and `source` for direct source generation. The original six archives below the historical heading retain their original mode names and bytes.

The fixture was frozen at `8dd85545c0ebbf37f441d436179c67cbbe4d8be4` before any endpoint was queried. The original evaluator imports `workFile` and the stock `endpoint` at `8d1812c08881131898bdb1412ac50aa8f0c963ce`. Each arm and mode starts a fresh session per project, carrying its own workspace into the follow-up. Full-context and direct-source modes disclose the selected path, goal and entire visible project from the start. Each policy receives the current status and gets eight decisions of up to eight tokens each. An edit asks the same checkpoint for up to 384 tokens of verbatim source. The direct-source ablation uses one such source call per request. Each prompt is a single stock user message, greedy, with thinking disabled. Each finished turn runs the visible suite and every hidden check through that turn in separate fresh containers. A cumulative pass requires all hidden checks due at that turn to pass with at least one executed Bun test. The reporting fix at `436afa8` concerns a read after a write. No historical policy reached a write. Scores use executed acceptance checks.

Use Bun 1.4.4, Docker sandbox `cwm-bun-project:1.4.4` (observed image ID `sha256:b98507ea09465f02a0f6dfc3a4dab90da4c149e9cdfec463de4e780549ef33a4`), and CPU llama.cpp b6602 (`72b24d96`). The Q8_0 base SHA-256 was `0dc7638539067268774c275a14a6ec9c7e01f7eeb2cff606c8590361fa527e4c`. C2 loaded the FP32 LoRA at `b38ed45365142e7cb00e3aa8c7fa5def5c1543df`, verified SHA-256 `55a828fd72c3d1520e8d3668313c0b50dfbad48b99e8729ec251cf9ed44682cb`. B2 loaded the FP32 LoRA at `528437e2e7ef214c3630bb36153e5947309b9a4f`, verified SHA-256 `59ca775a59293b551206d7f7ff500b9b2a403792e617076cdfb62a3900a0096b`. A used the base alone. All three servers used `--alias blind-cwm --jinja -c 8192 --parallel 1 -t 6 -tb 6 --seed 1`. From `cwm`, run one command per arm and mode against its matching server with a fresh destination.

```sh
bun bench/development/c2-evaluate.ts "$ENDPOINT" blind-cwm "$ARM" "$MODE" "$OUT.json.gz"
```

Time covers each production turn, including any in-turn visible test. Post-turn grading and server startup are excluded. These are single-run wall times. For historical context, the original A project policy recorded 225.24 s across six turns (median 39.03 s, 43 calls, 39,199 input and 3,129 generated tokens). That policy allowed eight JSON-grammar decisions with 768 tokens each. The earlier directed A evaluation recorded 35.28 s across four turns (median 8.77 s, six calls, 1,979 input and 570 generated tokens), with up to two 768-token source attempts and a test diagnostic on retry. Both used different fixture lineages and interfaces. [Original measurements](https://github.com/ethan-wickstrom/experiments/tree/436afa8952ea96ac7cced9a842f569085f018945/cwm/bench/development/results)
