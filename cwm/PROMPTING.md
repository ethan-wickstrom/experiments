# Prompting the TypeScript CWM

Start from the question you want answered. A coding request needs a draft and an intended behavior. A simulation needs source and a call. A next-pause question needs source and the state the debugger currently shows. The CLI keeps those inputs distinct and lets you move between them in one session.

## Work on a project

From the `cwm` directory, install the locked dependencies, build the disposable Bun test image, and serve the joint coding and execution adapter. Download the official base once using the [local server instructions](#local-model-server). This setup uses Docker, Bun 1.4.4 and llama.cpp b6602.

```sh
bun install --frozen-lockfile
docker build -f project/Dockerfile -t cwm-bun-project:1.4.4 .
base="$HOME/.cache/typescript-cwm/MiniCPM5-1B-Q8_0.gguf"
llama-server -m "$base" --lora bench/development/C/adapter-f32.gguf \
  --alias minicpm5-joint --jinja -c 16384 -t 4 -tb 4 --parallel 1 \
  --host 127.0.0.1 --port 8082
```

In a second terminal open a small project. Use a dedicated working copy. Writes change its TypeScript files immediately. The workspace assumes a single writer during each turn. It refreshes at the next request, checks for stale bytes before replacing a file, and uses an atomic rename. Concurrent mutation of files or directory entries during those checks is outside the persistence guarantee.

```sh
bun run project /path/to/project
```

Type a goal such as `Make the board restore its saved lanes from the local JSON file.` Then give a follow-up such as `Keep persistence working and fix the duplicate task after a move.` The policy chooses from reads, writes, tests and done, with eight decisions per turn. The JSON action grammar limits repeated reads and tests. The tool returns file bytes, a write acknowledgment, or the actual test status and a bounded diagnostic. Hidden benchmark suites live outside the project supplied to the model.

- `/edit board.ts REQUEST` selects the file explicitly and asks the checkpoint for complete replacement source. After a failing real test it gets one repair attempt.
- `/work board.ts REQUEST` starts each request with the selected path, goal and an empty file list. A model decision of `read` observes the visible project in sorted path order. Subsequent decision and source calls receive those bytes, updated after accepted writes. A test supplies a pass/fail status to the decision and records a bounded diagnostic in history. To try it, use the server command above with `bench/development/c2/C2/adapter-f32.gguf` in place of the rank-16 adapter. [Blind evaluation and historical full-context ablation](bench/development/c2-results/README.md)
- `/forecast {"op":"test"}` asks the same checkpoint to predict the current tests. A candidate `write` asks about replacing a file and then running the tests. This command neither writes nor executes.
- `/quit` closes the project session. The server in the first terminal has its own lifetime. Set `CWM_PROJECT_URL` and `CWM_PROJECT_MODEL` to address another local instance.

The sandbox sends project bytes into a fresh unprivileged container with no host mounts or network. It provides Bun and the installed Effect package. The workspace supports up to 128 UTF-8 source, JSON and Markdown files, each at most 64 KiB. Writes are limited to TypeScript. A model's `done` and a visible test pass each have their own meaning. Check the changed source and independent behavior before relying on it. [Held project transcripts and limits](bench/development/evaluation.md)

## Write and revise a function

From `cwm/`, install dependencies with `bun install --frozen-lockfile`. Use Bun 1.4+ and Node 24.11+ on your PATH. To enable natural language and neural next-pause queries, start the local server below. Then run `bun run chat` in a second terminal. Paste these lines one at a time:

```text
/case {"args":[12,3],"returns":36}
Write a function that returns the total ticket price given a unit price and the number of tickets.
/predict [7,5]
/verify [7,5]
/case {"args":[12,3],"returns":38}
Now add a flat booking fee of two to the total. Use one return expression.
/verify [7,5]
/source
/save ticket.ts
```

In a live CPU session the adapted checkpoint wrote `return unitPrice * numTickets;` and revised it to `return unitPrice * numTickets + 2;`. The structured model predicted 35 and 37 for the unprompted arguments. Both function frames and the terminal outcome matched fresh V8 observations for each draft. In another session the generated revision used a temporary `const`; the structured predictor abstained, and V8 returned 37. Generation is sampled.

`/case` replaces a case with the same arguments. Distinct argument lists accumulate. `/clear` clears the examples. A request always acts on the current working draft and can use the most recent assessment, prediction, or verification as feedback. A source parse or server error preserves the previous draft. Use `/source` to inspect the draft before executing it. `/save` writes a new file. Reopen an existing one with `bun run chat ticket.ts run`; the export name defaults to `run`.

### Local model server

Download the official ~1.15 GB quantization once. The small trace-trained adapter is in this repository. The following ran on CPU with llama.cpp build b6602. Use the `llama-server` binary for your platform on PATH. [llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases/tag/b6602) · [MiniCPM deployment guide](https://github.com/OpenBMB/MiniCPM/blob/main/docs/deployment/llama_cpp.md)

```sh
mkdir -p "$HOME/.cache/typescript-cwm"
base="$HOME/.cache/typescript-cwm/MiniCPM5-1B-Q8_0.gguf"
curl -fL --retry 3 https://huggingface.co/openbmb/MiniCPM5-1B-GGUF/resolve/5385560dd3e232bcc3577fd9442c332cad2facbd/MiniCPM5-1B-Q8_0.gguf -o "$base"
llama-server -m "$base" --lora bench/minicpm/cwm-minicpm5-lora-f32.gguf \
  --alias typescript-cwm-minicpm5 --jinja -c 8192 --parallel 1 --host 127.0.0.1 --port 8080
```

The base SHA-256 is `0dc7638539067268774c275a14a6ec9c7e01f7eeb2cff606c8590361fa527e4c`. The CLI sends source, requests, examples and feedback to the local chat-completions endpoint. Set `CWM_CHAT_URL` and `CWM_CHAT_MODEL` to select your own server and model alias. The server controls which weights actually run. The Python reference supports direct prompting, retraining and scoring. [Adapter experiment](bench/minicpm/README.md)

## Ask what a program will do

Open a source file and enter `/predict [7,2]`. The structured CWM fits once at startup on 54 frozen oracle invocations from the varied-layout and targeted-join training sets. It gets the current source and arguments, predicts entry, then feeds each predicted frame back as the next input. Each frame carries an event kind, source coordinates, stack, and locals with projection flags. `terminal` includes the predicted outcome. `unseen` means the model ran out of evidence. `limit` means the 128-transition budget ran out. These commands work without a language-model server.

`/verify [7,2]` first runs the structured forecast, then **executes the current source** in the existing trusted-code oracle. The comparison starts at the observed function entry and reports the number of consecutively matching whole frames, whether the outcomes agree, and whether the entire call matched. The module prefix remains visible in the observed trace. Run this command only on source you trust. [Oracle contract](README.md#what-the-oracle-observes)

## Specify an intermediate effect

Suppose an inventory function takes `stock` and `ordered`. It must debit stock and return the quantity ordered. A test of the returned quantity alone also accepts an implementation that **adds** stock. Save this draft as `inventory.ts`:

```ts
export function update(stock: number, ordered: number) {
  stock = stock + ordered;
  return ordered;
}
```

Run `bun run chat inventory.ts update` and enter:

```text
/case {"args":[7,2],"returns":2,"visits":[{"stock":7},{"stock":5}]}
/check
/repair
/verify [7,2]
```

Each visit must match a distinct predicted frame in order. A visit can constrain several locals at once, and each specified local must be an exact snapshot. The original draft fails the second visit. The planner tries the repository's reversible single AST edits and finds that changing addition to subtraction satisfies both visits and the return. It emits the original assessment, the exact edit and the selected source. V8 independently reproduced the repaired trajectory.

A language proposal goes through the same planner. A draft that already matches every example is retained. If the original misses, exactly one distinct edited source must satisfy every example for the planner to apply it. `ambiguous` reports multiple matching edits. `unresolved` reports zero matching edits. In both cases the incoming proposal stays available for inspection or another revision. `unconstrained` means no cases were supplied. Passing finite cases says only what the predictor found on those calls.

## Directly prompt the trace-trained weights

Open a file containing a single exported function with integer parameters `x` and `y`. Enter `/resume S,2,1,2,3` if the debugger is paused at line 2, column 1 with `x=2` and `y=3`. The CLI sends the complete source, current state and `resume` action in the format used for training. It prints the neural answer and whether generation reached a stop token or its token limit. The output language is `S,line,column,x,y` for a step or `R,line,column,x,y,value` for a return. Coordinates start at one. This experiment is conditional on another function pause existing.

On 34 held-out resume prompts the full-precision adapter got one entire row right and missed all 12 local updates. We repeated the 34 prompts with the Q8 server configuration above and observed the same whole-row counts (base zero, adapter one).

The structured CWM learns operator, predicate and pause-location rules and drives the behavior checks and repair search. It supports a single synchronous scalar function with parameter assignments, returns, braced branches and loops. Temporary variable declarations, heap objects, async work, and general multi-file edits exceed its current scope. [Recurrent evaluation](bench/recurrent/README.md)

Meta's prompting guide puts source and typed trace events into a model-specific language. Here the user supplies the host call explicitly, since source alone leaves the initial parameter values undetermined. The neural resume prompt records an action between observations, as in the paper's function-tracing experiment. Editing and oracle verification each have their own action because they change different things: the source under consideration and the evidence about its behavior. [Meta prompting guide](https://github.com/facebookresearch/cwm/blob/main/PROMPTING_GUIDE.md) · [CWM paper](https://arxiv.org/abs/2510.02387)
