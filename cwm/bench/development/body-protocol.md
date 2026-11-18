# Function-body completion on the original project tasks

Use the original offline task board, Unicode line editor and ordered sample reader, their original visible files and both original requests. The follow-up inherits the first turn's actual files even after failure. Collect C2, unchanged A, and B2 on all six turns each. B2 supplies the matched coding-only control for joint training. These previously published tasks measure transfer to the original projects under a new interface. They are not a new blind dataset.

## Interaction

The host supplies the sole implementation path. The model chooses the export on the three-function board using a 24-token grammar restricted to exported names. The editor and reader have one eligible export each. Run the actual visible tests before editing. Give the checkpoint the current request, visible file contents, function choice and compact actual diagnostic in one stock no-thinking user message. Prefill the assistant with a TypeScript fence and the source declaration through its opening brace and original line break, when present. All body bytes after that come from greedy raw llama.cpp completion, capped at 384 tokens, stopping at EOS or a newline followed by a closing fence. Parse up to the first complete body in its original context with Oxc. Discard any generated suffix after that body and retain it in the raw transcript. An invalid or capped completion ends the turn. Surrounding source bytes are preserved.

Before applying each valid edit, ask the same checkpoint for its forecast using the existing write/test forecast prompt and eight tokens. This forecast is logged independently and cannot select, reject or repair a candidate. Apply the write and run the visible suite. Only an actual visible failure following an accepted write permits a second attempt on that export, with its current body and updated diagnostic. Stop after the second test. Each turn records the choices, exact rendered/tokenized prompts, model continuations, writes, tests, raw cumulative hidden runs, and token and wall-clock costs. Execute the final visible suite independently. A solved turn requires a changed accepted write, passing visible tests and every independent suite through that turn passing. Report cumulative hidden grades even if the policy made no successful edit.

The evaluator counts completed model responses and failed forecast attempts separately. Token totals cover completed responses. For a failed forecast, the host records elapsed time and the error. A transport error can leave server-side generation and usage unknown. All forecast calls in the archived held runs returned a response.

## Reproduction

From cwm, build the Docker image using the project Dockerfile. Use llama-server b6602 (72b24d96), the pinned MiniCPM5 F16 GGUF (68c40b08b1242754a107b9510af89aa75b10c75843ca7844643c70956b7f1e3d), and one server at a time. For C2 and B2 use the adapter GGUF and SHA-256 from their existing c2 artifact manifests. A uses the same F16 base with no adapter. Use the following commands with the appropriate model alias and adapter. The server origin must support llama.cpp's template, tokenizer and raw completion endpoints.

```sh
llama-server -m "$F16" --alias "$MODEL" --jinja -t 4 -tb 4 -c 4096 \
  --parallel 1 --host 127.0.0.1 --port 8085 --lora "$ADAPTER"
# Omit --lora and its argument for A. Run each checkpoint separately.
for project in offline-task-board unicode-line-editor ordered-sample-reader; do
  bun bench/development/body-evaluate.ts http://127.0.0.1:8085 "$MODEL" "$ARM" "$project" "$OUT"
done
```

An initial C2 development trial on the training outline library failed. Retaining the declaration's first line break and the training prompt's file-list representation produced executable edits on outline, receipt, weave, playback and composer. Only playback passed. Keep every development trial. Freeze the interface before collecting any body completions on the three original held projects. No training, candidate ranking, reference edits, hidden test feedback or checkpoint selection is part of this experiment.
