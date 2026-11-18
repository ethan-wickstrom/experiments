# Editing one function body on the original projects

C2 solved the playback training-library control, then failed all six original project requests. The matched F16 base and coding-only B2 failed the same six. Each checkpoint also failed every end-of-turn visible suite and all nine individual hidden suite runs. The projects were previously published. The function-body interface, models, caps, repair rule and grader were frozen before collecting the held transcripts. [Protocol and reproduction](../body-protocol.md) · [Original project fixtures](../held.ts) · [Development transcripts](development.json.gz)

| Checkpoint       | Solved turns | Writes / writes changing bytes | Correct test forecasts | Model calls | Input / output tokens | Turn time, total |
| ---------------- | ------------ | ------------------------------ | ---------------------- | ----------- | --------------------- | ---------------- |
| A, unchanged F16 | 0/6          | 12 / 1                         | 5/12                   | 26          | 16,366 / 388          | 197.47 s         |
| B2, coding only  | 0/6          | 8 / 4                          | 0/8                    | 20          | 12,840 / 460          | 163.00 s         |
| C2, joint        | 0/6          | 6 / 3                          | 3/6                    | 17          | 10,323 / 987          | 188.43 s         |

The host selected the sole implementation file in each library. All three models selected `move` on the board persistence request. C2 wrote the same body after receiving a failing test. It predicted failure on the first write and success on the second. The editor and reader each had only one eligible export. Both C2 editor continuations hit the 384-token cap. Its first reader turn wrote and tested twice, and its second returned an invalid body. [Board](C2-offline-task-board) · [Editor](C2-unicode-line-editor) · [Reader](C2-ordered-sample-reader)

Every accepted write underwent a forecast and visible test, including byte-identical writes. Two A forecasts and five B2 forecasts were outside the accepted vocabulary or incomplete. All six C2 forecasts were in the vocabulary. Every observed write led to a visible failure. The forecast denominator includes invalid predictions. Elapsed time includes model calls, initial visible diagnostics, writes and in-turn tests. Server startup and independent grading are excluded. The checkpoints ran serially on the same VM with four CPU threads.

In development, the first outline trial failed. The frozen prompt retained the declaration's first line break and used the training file-list representation. It passed playback and failed outline, receipt, weave and composer. A separate `/body playback.ts seek Select a track by wrapping the index.` session persisted the generated body and passed the Docker test. Its pre-write forecast was wrong. The CLI caller explicitly selected `seek`. [CLI transcript](development-cli.json.gz)

Each turn file contains raw completion text, input and output token IDs, timings, source before and after each write, pre-write predictions and observed visible and hidden output. All 63 held prompts matched the stock release's rendered text and token IDs when checked independently with Transformers. The original published score files and graders retain their original bytes.
