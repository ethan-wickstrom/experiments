# Does the site key distinguish the action?

**Yes on controlled contrasts; no evidence of composition.** The [previous anchors](sites.ts) retain AST kind, occurrence and position but can discard the source text: their synthetic filename has no corresponding source. Training only on `return x+y` gave the operand-anchor model the right return site but value **10** for a renamed `return x-y` on `(7,3)`; V8 returned **4**. The candidate abstained without subtraction evidence.

[Meta's debugger](https://github.com/facebookresearch/cwm/blob/7930e0298bf32aae28cc0e35e18a54c772603364/demos/cwmdbg.py#L159-L180) supplies source and frame actions. Its [guide](https://github.com/facebookresearch/cwm/blob/7930e0298bf32aae28cc0e35e18a54c772603364/PROMPTING_GUIDE.md#trace-prediction) distinguishes action, observation and returned value. We test that distinction in a smaller model: the [candidate](action.ts) keys a statement by its Oxc expression tree, including operator, operand order and literal value. Bindings are numbered by declaration order in one lexical scope; **the same slots encode and decode actual frame locals**. For example, `left-right` uses slots 0 then 1, while `right-left` uses 1 then 0. This is not an evaluator. Retrieval, affine fitting and abstention are unchanged.

**Scope:** a single exported synchronous function with identifier parameters, simple `const` declarations and returns of supported expressions. Sites are reversible statement/operand starts, not arbitrary columns. Unknown syntax, unmappable sites and missing successors abstain. No claim about lexical shadowing, closures or arrays.

## Protocol

[Cases fixed before scoring](https://github.com/ethan-wickstrom/experiments/commit/41a63de1c). Nine training bodies × five integer pairs. Nine positive controls repeat the training actions on the seen input `(7,3)` under a renamed file, whitespace edits and consistent binding renames. They check representation, **not new-input generalization**. The contrasts cover addition/subtraction/swapped subtraction, less/greater-than and adding 2/5. For each control, replay asserts that the predicted step → return frame, including value and query locals, equals V8's.

Four **fresh compositions**, each on `(7,3)` and `(4,1)`: swap the continuations between `const z=x-y; return z+2` and `const z=x+y; return z-5`; nest subtraction inside addition; compare a sum with a literal. No post-score candidate changes to fit them. Scoring receives only the source/entry identity and current frame. Teacher-forced transitions include module initialization; complete rollouts start at observed function entry and then self-feed. Correct nonterminal counts exclude the separate terminal outcome.

| Split    | Model                                   | Correct | Wrong | Abstain | Correct nonterminal | Complete rollouts |
| -------- | --------------------------------------- | ------: | ----: | ------: | ------------------: | ----------------: |
| Controls | Source / filename-blind / syntax (each) |       0 |     0 |      29 |                   0 |               0/9 |
| Controls | Syntax+operands / return readout (each) |       9 |     0 |      20 |                   0 |               0/9 |
| Controls | Action                                  |      20 |     0 |       9 |                  11 |               9/9 |
| Fresh    | Source / filename-blind / syntax (each) |       0 |     0 |      28 |                   0 |               0/8 |
| Fresh    | Syntax+operands / return readout (each) |       8 |     0 |      20 |                   0 |               0/8 |
| Fresh    | Action                                  |       4 |     0 |      24 |                   0 |               0/8 |

A known operator is not a known transition. A predicted successor must map back to the query program; the old continuation is absent in the swapped programs, and the nested return trees have no matching training action. Returning the value already visible at a return stop does not establish execution prediction. Keep the candidate out of production.

Replay from `cwm/` with Bun 1.4.4 and Node 24.19.0:

```sh
bun install --frozen-lockfile
bun bench/action-experiment.ts
```

This recollects only the 62 small traces. It does not rerun or revise the historical 1,024-run benchmark.

**Oracle qualification.** With Bun 1.4.4 and Node 24.19.0, ordinary execution returned 0 calls for each custom Error getter (`stack`, `name`, `message`); the old tracer returned 3 for each and the revised tracer returned 0. The revised differential tests also passed with Node 26.13.1. These are counts for these fixtures, not a universal bound on engine behavior. In the collector's three-worker regression, a fatal second input previously allowed the third to publish; the fix leaves its getter unread and its shard absent, and the first shard exists before rejection.
