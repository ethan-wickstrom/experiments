# Diagnostic-conditioned AST editing with MiniCPM5-1B

Across four requests in two independently sealed multi-module projects, all four arms completed their 32 calls and solved zero turns. No candidate passed even the visible suite. The only live success was a development example. A, B2 and C2 each produced the same correct freight calculation on proposal 3, before receiving a diagnostic. C2 reproduced that edit in a fresh on-disk CLI workspace.

## Held results

Each proposal occupies one slot, including truncations, invalid fragments and repeated source. A new test is a changed source actually executed in a fresh visible sandbox. Reuse means the candidate matched a source with a recorded run. Coverage counts turns with any candidate passing all visible and cumulative hidden checks. A miss is a covered turn whose selected workspace failed. Time sums the four interactive turns and excludes retrospective hidden grading. Different server/cache histories make these descriptive wall times.

| Arm            | Solved | Coverage | Misses | New tests | Reused | Invalid | Capped | Prompt tokens | Generated tokens | Seconds |
| -------------- | ------ | -------- | ------ | --------- | ------ | ------- | ------ | ------------- | ---------------- | ------- |
| A-feedback     | 0/4    | 0/4      | 0      | 5         | 14     | 13      | 0      | 29642         | 898              | 233.8   |
| B2-feedback    | 0/4    | 0/4      | 0      | 8         | 9      | 14      | 1      | 29640         | 1014             | 305.3   |
| C2-feedback    | 0/4    | 0/4      | 0      | 4         | 13     | 13      | 2      | 29670         | 1114             | 188.0   |
| C2-no-feedback | 0/4    | 0/4      | 0      | 4         | 14     | 12      | 2      | 23002         | 1094             | 133.8   |

The feedback-enabled arms each delivered actual failing Bun diagnostics on all 16 repair calls. C2's first round produced 16/16 byte-identical replies across the two arms. Diagnostics changed eight of the 16 second-round replies. Each C2 arm executed just one new second-round source, on the intake follow-up. With feedback C2 changed the owner property to `mapToOwner`. Without it C2 changed a nullish-coalescing operator to logical AND. Both edits failed. Feedback added 6,668 prompt tokens in this run. The absence of a passing candidate prevents measuring selection quality on this suite.

## Candidate outcomes

Each cell gives the proposal status followed by visible/hidden **test cases passed**. The available column gives the corresponding total numbers of cases. Hidden counts sum across the separate suites through the current turn. T means a new AST splice was executed. U means the proposal reused its parent or the turn's starting source. I means invalid and L means generation reached the 128-token cap. The first four calls use the original source. The final four use the first tested draft, falling back to the original when necessary.

| Arm            | Project and turn | Available V/H | 1     | 2     | 3     | 4     | 5     | 6   | 7     | 8     |
| -------------- | ---------------- | ------------- | ----- | ----- | ----- | ----- | ----- | --- | ----- | ----- |
| A-feedback     | copy-counter 1   | 2/3           | T 1/2 | I     | T 1/2 | U 1/1 | U 1/2 | I   | U 1/2 | I     |
| A-feedback     | copy-counter 2   | 4/6           | U 2/1 | U 2/1 | T 2/1 | I     | U 2/1 | I   | U 2/1 | I     |
| A-feedback     | intake-desk 1    | 2/3           | U 1/2 | I     | U 1/2 | I     | U 1/2 | I   | U 1/2 | I     |
| A-feedback     | intake-desk 2    | 3/6           | U 1/3 | U 1/3 | U 1/3 | I     | T 1/3 | I   | T 1/3 | I     |
| B2-feedback    | copy-counter 1   | 2/3           | T 1/2 | I     | U 1/1 | I     | U 1/2 | I   | U 1/2 | I     |
| B2-feedback    | copy-counter 2   | 4/6           | T 2/1 | I     | T 2/1 | I     | T 2/1 | I   | T 2/1 | I     |
| B2-feedback    | intake-desk 1    | 2/3           | U 1/2 | I     | U 1/2 | I     | T 0/0 | I   | U 1/2 | I     |
| B2-feedback    | intake-desk 2    | 3/6           | T 1/3 | U 1/3 | T 1/3 | I     | U 1/3 | I   | U 1/3 | L     |
| C2-feedback    | copy-counter 1   | 2/3           | U 1/1 | I     | T 1/2 | I     | U 1/2 | I   | U 1/2 | I     |
| C2-feedback    | copy-counter 2   | 4/6           | T 2/1 | I     | U 2/1 | I     | U 2/1 | I   | U 2/1 | I     |
| C2-feedback    | intake-desk 1    | 2/3           | U 1/2 | I     | T 1/1 | U 1/2 | U 1/1 | I   | U 1/1 | I     |
| C2-feedback    | intake-desk 2    | 3/6           | L     | U 1/3 | U 1/3 | U 1/3 | L     | I   | T 1/3 | I     |
| C2-no-feedback | copy-counter 1   | 2/3           | U 1/1 | I     | T 1/2 | I     | U 1/2 | I   | U 1/2 | I     |
| C2-no-feedback | copy-counter 2   | 4/6           | T 2/1 | I     | U 2/1 | I     | U 2/1 | I   | U 2/1 | I     |
| C2-no-feedback | intake-desk 1    | 2/3           | U 1/2 | I     | T 1/1 | U 1/2 | U 1/1 | I   | U 1/1 | U 1/1 |
| C2-no-feedback | intake-desk 2    | 3/6           | L     | U 1/3 | U 1/3 | U 1/3 | L     | I   | T 0/1 | I     |

The first repair parents, numbered as in the table, were (1, 3, original, original) for A, (1, 1, original, 1) for B2 and (3, 1, 3, original) for both C2 arms. Each arm ran on its own lineage. No arm persisted an edit on the first turn, so both second turns inherited a failing prerequisite in a different module from the newly selected target.

## Where the budget went

- Of 128 held proposals, 21 produced new, executable sources, 50 reused source, 52 were invalid and five were capped. All 17 new edits in the feedback-enabled arms changed member names. The models repeatedly chose fields or methods absent from the visible project. Across all arms 49 of 52 invalid replies copied literal span markers into their output. Sandbox runs and model replies are preserved for every slot.
- The printer request concerned rounding sheets separately for each copy. C2 changed the declared `job.duplex` access to `job.sides` despite receiving the full interface. On the follow-up it proposed `job.sliceCentsPerSheet` where a computed sheet count was available. The intake request required preserving whitespace trimming during capitalization-insensitive lookup. C2 proposed `slice` for `trim`. These examples show grounding and edit-localization failures with relevant modules present.
- All 128 calls fit the 96-site / 24,000-byte limits and returned endpoint responses. Observed prompts ranged from 609 to 1,347 tokens. The editor permits single-span replacements in one named module per call and one provisional repair parent. It cannot directly append a chained call to the complete return expression in the intake normalization helper. The provided property site can rename `trim`, and the equality operands elsewhere offer alternative edit sites. Braced and multi-line expression replacements are also outside the schema. There was no endpoint context overflow or sandbox infrastructure error.
- A, B2 and C2 all failed the held turns at the matched budget. These four dependent requests provide no demonstrated checkpoint advantage. Changing model weights, receiving test output and selecting by actual tests are distinct interventions. The A/B2 controls were registered after the C2 feedback run, before seeing either control on these projects.

## Development and demonstrator

The six C2 pilot archives preserve every attempt on freight pricing and staff badge capitalization. Pilot 1 returned eight invalid proposals, often full functions. Pilot 2 constrained replacement syntax, pilot 3 returned an edited line, and pilot 4 named replacement operators in English. None passed a development task. Pilot 5 constrained operator families and increased the budget from four to eight calls. It still passed neither. Pilot 6 excluded previously tested operator edits from the available menu and validated each returned line against its site pattern. The first freight edit subtracted, failed and became unavailable on the initial source. The next operator proposal multiplied and passed the visible example. The final selection wrote that source and confirmed it in another sandbox. No candidate passed the badge example.

On the retrospective development controls A and B2 each also solved freight on proposal 3 and failed badge. This success is reproducible with the released base under operator diversity and visible-test selection. It supplies no evidence of a joint-training advantage or a diagnostic-driven solution. Freight and badge each have just one visible development example. The separate CLI transcript records real C2 inference, verification exit zero and the persisted multiplication source. To use the editor interactively, start the project CLI with the C2 endpoint and enter `/splice PATH REQUEST`.

## Freeze, isolation and replay

The editor commit is `afc72ae` on the branch from `51ab0af`. The independent author sealed fixtures at `85d3f22`. The editor and primary [protocol](PROTOCOL.md) were frozen at `35323bc` before that fixture was revealed. The integrated fixture tree is byte-identical to the author's commit. A separate [control specification](CHECKPOINT-CONTROLS.md) at `fb30304` froze the held A and B2 comparison. Checkpoint hashes, container ID and server options are in those documents.

The evaluator adds only the supplied visible tests, the target and the request to each project. Independent cumulative tests execute in separate post-selection sandboxes. They never update session history. Run `bun bench/development/splice-results/audit.ts` from CWM to verify the saved source states, goals, diagnostics, candidate reconstruction and grade arithmetic against all 128 prompts. Reproduce a held run with the protocol command and the appropriate checkpoint port. The four held archives use the arm names in the table. The development archives and CLI transcript are separate from the held scores.
