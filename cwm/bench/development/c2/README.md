# Directed source and joint execution adaptation

C2 is a rank-32 LoRA on the unchanged [MiniCPM5-1B release](https://huggingface.co/openbmb/MiniCPM5-1B/tree/ac83f813ba7da263c51a9f3ec37c2072597e54af). The host selects a path. One model call chooses a decision, and a separate call writes a complete raw TypeScript file. The same weights forecast a candidate write's downstream Bun outcome and the next native V8 pause. B2 is the policy-only comparison using the same interface, cache, rank, base, seed, optimizer, number of updates and loss-position budget. A is the unchanged base. [Protocol](protocol.md) · [Wire functions](wire.ts)

## Load and prompt

Download the release F16 base once. Its verified SHA-256 is `68c40b08b1242754a107b9510af89aa75b10c75843ca7844643c70956b7f1e3d`. Pass one LoRA to llama-server. Each GGUF contains exactly two FP32 tensors with all 196,608 trained coefficients checked against PEFT. [Base GGUF](https://huggingface.co/openbmb/MiniCPM5-1B-GGUF/resolve/5385560dd3e232bcc3577fd9442c332cad2facbd/MiniCPM5-1B-F16.gguf) · [C2](C2/artifacts.json) · [B2](B2/artifacts.json)

```sh
# From cwm/bench/development/c2
curl -fL -o MiniCPM5-1B-F16.gguf "$(jq -r .base_gguf_url C2/artifacts.json)"
printf '%s  %s\n' "$(jq -r .base_gguf_sha256 C2/artifacts.json)" MiniCPM5-1B-F16.gguf | sha256sum -c -
llama-server -m MiniCPM5-1B-F16.gguf --lora C2/adapter-f32.gguf --jinja --reasoning off -c 4096
```

Use the exported `edit(goal,path,files)` and `decide(goal,path,files,status)` functions to produce the single user message. They preserve exact file bytes, sort paths, and serialize JSON reversibly. C2 forecast calls use the existing forecast instruction with a newline and `jsonState({files,history,candidate})`. The shared serializer escapes all less-than characters and slashes opening thinking directives. Normal JSON parsing restores the original strings. The trainer appended each assistant answer to the exact release generation prefix with thinking disabled. It checked every input and every raw answer for embedded control IDs and verified exact decoding through the final newline.

The PEFT command accepts the exact same user-message text on stdin. It emits raw bytes only when the stock server stop was generated. Both release EOS IDs are accepted. No fence handling or whitespace trimming is applied.

```sh
bun -e 'import {edit} from "./wire.ts"; process.stdout.write(edit("Add one to the input.", "next.ts", [{path:"next.ts",text:"export const next = (n: number) => n;\n"}]))' | python inference.py C2
```

For actual follow-ups, replace the goal and use the project state after the last observed edit. A directed source call receives the complete visible source and visible tests. The compact decision receives an explicit host observation status. On the training trajectory it maps unread to read, read to test, fail to edit, written to test, and pass to done. That status-to-action mapping alone can solve the decision labels. This experiment supplies no evidence of autonomous path selection.

## Data and matching

The ten authored families cover Markdown outlines, interval ordering, mailbox deduplication, receipt formatting, paired sequences, paragraph parsing, inventory aggregation, playlist rotation, label composition and grid transforms. Their source shapes include named exports, arrow exports, separately exported functions and an imported helper. Each has three successive goals. A second requirement forks at every goal. Both branches start from identical source bytes and use the same two plausible candidates. Bun tests them in both contexts, reversing which candidate passes. The collector restores the starting bytes between candidates and independently reruns the accepted result. Only the accepted first branch continues to later goals. Each plan-changing user request replaces the visible behavior check. Families have one small visible assertion per requirement.

There are 60 directed source rows (2,233 target tokens including stops), 300 decision rows (600), 140 forecast rows (300), and 98 native recurrent transitions (1,076). The forecasts comprise 60 passing and 60 failing candidate writes and 20 unread replacement rejections. Actual Bun stdout, stderr and exit status are retained independently of model examples. The longest sequence was 949 tokens. The cache kept every target position, reusing causal KV prefixes between neighboring prompts. A comparison against a full fresh forward pass on the longest prompt checked both cached features. The fitter also checked live adapter logits after optimization.

Both fits performed 512 updates of 64 positions, 32,768 total, with AdamW at 0.001 and seed 17. C2 used 18,432 raw source, 4,096 decision, 6,144 paired pass/fail forecast, 1,024 rejection, and 3,072 native execution positions. Forecast sampling excluded answer stops. B2 reallocated the entire forecast/execution budget in the same 9:2 source-to-decision ratio, with the nearest feasible cumulative integer allocation (26,810 source, 5,958 decision). Consequently B2 has more policy rehearsal. Training used eight CPU threads, FP32 and the two-factor low-rank update on layer 23's MLP down projection. The shipped checkpoints contain both matrices, AdamW moments, sampler state, torch RNG and training progress. Step 129 was replayed from disk and matched indices, loss and weights exactly. B2 also crossed the 128/129 boundary in a fresh Python process.

## Reproduce

Use the [existing pinned CPU environment and checkpoint setup](../README.md#reproduction) with eight threads and the specified Bun and Node versions. Run commands from this directory. Source templates, checks, and alternative implementations are trusted authored material. Any model-generated file evaluated by the diagnostic runner executes in a separate non-root, read-only, network-disabled Bun container with resource limits and only ephemeral probe files mounted.

```sh
work=$(mktemp -d)
bun collect.ts "$work/data"
cmp <(gzip -dc "$work/data/projects.jsonl.gz") <(gzip -dc data/projects.jsonl.gz)
python cache.py "$work/c2-features.pt"
python fit.py --arm C2 --cache "$work/c2-features.pt" --out "$work/C2"
python fit.py --arm B2 --cache "$work/c2-features.pt" --out "$work/half" --stop-at 128
python fit.py --arm B2 --cache "$work/c2-features.pt" --out "$work/B2" --resume "$work/half/state.pt"
for arm in B2 C2; do
  cmp "$work/$arm/peft/adapter_model.safetensors" "$arm/peft/adapter_model.safetensors"
done
bun test c2.test.ts
python -m unittest -v test_weights
```

Run the [official conversion wrapper](package_model.py) against llama.cpp revision `a300a9c33462f23d9d61e951650d249486f2b0f6`. From an experimental checkout, `python package_model.py /path/to/llama.cpp C2 /path/to/MiniCPM5-1B-F16.gguf` re-exports C2, verifies tensors against PEFT, and writes a manifest. The [server check](server_check.py) compares the running server's rendered bytes, IDs, prompt token count, and response on one training edit. Invoke it against a running server with, for example, `python server_check.py C2 8080`. The independent native PyTorch and llama.cpp runtimes may generate different outputs.

```sh
bun probes.ts "$work/probes"
cmp <(gzip -dc "$work/probes/projects.jsonl.gz") <(gzip -dc probes/projects.jsonl.gz)
cmp <(gzip -dc "$work/probes/pauses.jsonl.gz") <(gzip -dc probes/pauses.jsonl.gz)
bash sandbox-image.sh
for arm in A B2 C2; do
  CWM_THREADS=4 python evaluate.py "$arm" > "$work/$arm.json"
done
```

These local probes use two new library families with eight directed edit requests, including follow-ups from verified source, four observed native executions on two new scalar programs, and additional Bun assertions absent from prompts. Test exit codes, generation stop reasons, raw text, forecast margins, goals and actual oracle outcomes remain separate. Each choice pair compares the pass-minus-fail first-token logit margin of two candidates conditioned on the same history. Both candidates were actually tested against that requirement. Self-fed pause rollouts start from observed entry and finish at predicted return, invalid output, repetition or the 16-step cap. The local FP32 diagnostic uses a 128-token source cap, a 32-token pause cap and an eight-token decision/forecast cap. The live directed interface allows longer source output. The integration runner separately evaluates the independently held live projects.
