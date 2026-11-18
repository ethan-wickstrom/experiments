# C2 diagnostic-conditioned AST editing

Frozen before revealing the projects at independent commit `85d3f22796d33b4f9e88ea15acf13f9f3711a7ff`. The fixture author knew the supported expression classes and multi-module requirement. They validated reference edits privately. No reference edit enters the generation process.

## Generation

Run the released joint C2 adapter on the MiniCPM5-1B Q8 base, llama.cpp b6602, stock chat, thinking disabled, 8,192-token context. Each project starts fresh per arm. Each turn adds the author's visible tests to the current workspace, including previously accepted edits, and names one target module. Read every visible file and retain all user requests. Run the initial visible suite in the existing offline Bun container.

Use four model calls on the initial state and four on the first changed, successfully executed candidate, even if an initial candidate passed. Fall back to the initial source if none executed. Within each round, alternate operator/property sites and other expression sites. Offer all available sites when a class is empty. Generate up to 128 tokens per call with the checked-in seeds and temperatures. The JSON schema binds the output to one site. For operators, offer grammar alternatives in the original operator family and omit already tested full source variants. For properties and expressions, supply surrounding source text with a marked span, receive an edited line, extract the fragment, and reparse the module to check its precise syntactic role and boundaries. Reuse the visible run for repeated source bytes.

Both arms use this same generation budget, repair parent, and visible test-based selection rule. On a failing second-round parent, the feedback arm additionally receives the actual exit code and suffixes of stderr (1,200 UTF-16 units) and stdout (200). The control omits that field. Only the first changed candidate passing a nonempty visible suite is written. Re-test the persisted file. No hidden result or source is available to the editor. Stop and record missing AST sites, or a prompt exceeding 24,000 UTF-8 bytes or 96 sites. Record endpoint and sandbox errors separately from invalid and truncated proposals.

## Grading

After each turn finishes, run the visible suite and execute each hidden suite through the current turn in isolation. Grade every reconstructible candidate on the same cumulative hidden suites. The workspace carried into the next turn reflects the editor's persisted choice. A turn passes if the visible run and all cumulative hidden suites pass. Candidate coverage counts turns having at least one passing candidate. A selection miss is a covered turn whose persisted workspace fails. Also report individual candidate status, visible passes, repair parent, hidden coverage, prompt and generation tokens, context limits, and failure modes. Raw outputs include invalid and duplicate proposals. Two lineages with follow-ups form a small descriptive evaluation.

## Reproduction

Start the pinned server with `--lora C2-f32.gguf --alias blind-cwm --jinja -c 8192 --parallel 1 -t 6 -tb 6 --seed 1` and the Q8 model. From the CWM directory, run the two modes sequentially with fresh output paths.

```sh
bun bench/development/splice-evaluate.ts "$URL" blind-cwm feedback feedback.json.gz
bun bench/development/splice-evaluate.ts "$URL" blind-cwm no-feedback no-feedback.json.gz
```

Base SHA-256 `0dc7638539067268774c275a14a6ec9c7e01f7eeb2cff606c8590361fa527e4c`. C2 adapter SHA-256 `55a828fd72c3d1520e8d3668313c0b50dfbad48b99e8729ec251cf9ed44682cb`. Sandbox `cwm-bun-project:1.4.4`, image `sha256:b98507ea09465f02a0f6dfc3a4dab90da4c149e9cdfec463de4e780549ef33a4`.
