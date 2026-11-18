"""Score one frozen arm on all fresh teacher-forced transitions and full self-fed trajectories."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from corpus import DATA, HERE, verified
from model import TRAIN, REVISION, adapted, examples, frame_row, generate, load, prompt, valid_row
from provenance import TRAIN_SHA, file_hash
from score import run

# Each control has a unique short answer. No generated code is executed.
CONTROLS = [
    ("What TypeScript primitive type is the expression 7 < 9? Reply with just the type.", "boolean"),
    ('In JavaScript, what string does "café".slice(0, 3) produce? Reply with that string only.', "caf"),
    ("In TypeScript, what number does [2, 4, 6].length return? Reply with just the number.", "3"),
]
LIMIT = 16


def rollouts(model, tok, traces):
    sequences = []
    for t in traces:
        gold = [frame_row(f,t["entry"],t["fn"]) for f in t["frames"][1:]]
        sequences.append(dict(args=t["args"], source=t["files"][t["entry"]], entry=gold[0],
                              gold=gold[1:], predictions=[], stop=None))
    for _ in range(LIMIT):
        live = [s for s in sequences if s["stop"] is None]
        if not live:
            break
        prompts = [prompt(s["source"], (s["predictions"] or [s["entry"]])[-1]) for s in live]
        for s, prediction in zip(live, generate(model,tok,prompts,limit=32), strict=True):
            prior = [s["entry"], *s["predictions"]]
            s["predictions"].append(prediction)
            if not valid_row(prediction):
                s["stop"] = "outside format/numeric domain"
            elif prediction.startswith("R,"):
                s["stop"] = "predicted return"
            elif prediction in prior:
                # Same source and state have the same greedy successor under this interface.
                s["stop"] = "repeated predicted state"
    for s in sequences:
        if s["stop"] is None:
            s["stop"] = "budget"
        equal_prefix = 0
        for output, expected in zip(s["predictions"], s["gold"]):
            if output != expected:
                break
            equal_prefix += 1
        s["prefix"] = equal_prefix
        s["exact"] = s["gold"] == s["predictions"]
    return sequences


def main():
    p = argparse.ArgumentParser()
    p.add_argument("arm", choices=("A","B","C"))
    args = p.parse_args()
    pins = json.loads((HERE / "artifacts.json").read_text())
    tape = DATA / "retention.jsonl.gz"
    digest = pins["retention_uncompressed"]
    rows = examples(tape, expected_sha=digest)
    training_sources = {r[0] for r in examples(TRAIN,expected_sha=TRAIN_SHA)}
    assert training_sources.isdisjoint(r[0] for r in rows)
    traces = list(map(json.loads, verified(tape,digest).splitlines()))
    base,tok = load(verify_local=True)
    model = base
    if args.arm != "A":
        path = HERE / args.arm / "peft"
        for name in ("adapter_config.json","adapter_model.safetensors"):
            assert file_hash(path / name) == pins[args.arm]["peft/" + name]
        model = adapted(base,path)
    result = dict(arm=args.arm, revision=REVISION, retention=digest,
                  transitions=run(model,base,tok,rows), rollouts=rollouts(model,tok,traces))
    answers = generate(model,tok,[p for p,_ in CONTROLS],limit=32)
    result["short_answers"] = [dict(prompt=p, target=target, generated=answer, exact=answer == target)
                              for (p,target), answer in zip(CONTROLS,answers,strict=True)]
    print(json.dumps(result,ensure_ascii=False,separators=(",",":")))


if __name__ == "__main__":
    main()
