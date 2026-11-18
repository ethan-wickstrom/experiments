# Source interventions at the first assignment

The earlier two-source debugger probe is retrospective. For confirmation, freeze the programs, inference settings and scoring before collecting new V8 traces. Each pair starts at the same function pause with the same locals. The two sources perform different assignments at that pause. The observed successor comes from a separate Node inspector invocation for each program and input.

| Intervention           | First variant           | Second variant          |
| ---------------------- | ----------------------- | ----------------------- |
| Operator position      | `x = x + y; y = y - x;` | `x = x - y; y = y + x;` |
| Operand order          | `y = (x - y) * x;`      | `y = (y - x) * x;`      |
| Assignment destination | `x = (x + y) * 2;`      | `y = (x + y) * 2;`      |

Use both argument lists `[6, 2]` and `[-2, 3]` for every variant. Use the same file, function name and return statement on both sides. Assert that the complete initial frames and next pause locations match across each pair, that both variants change locals, and that their successors differ. Keep failed preconditions visible.

Fit the existing structured model on the fixed execution tape with call-entry supervision disabled. Run the released base, joint and edit-only MiniCPM5 arms using their stock single-user execution prompt and 32-token greedy budget. Each prediction sees one source and its first function pause. Grade the next locals, complete next frame, and whether both complete frames in a pair are correct. Count capped or malformed replies as misses. Report the full denominator for each measure. The separately reported original four-run comparison also grades self-fed rollouts. Keep both probe sets outside training and model selection.
