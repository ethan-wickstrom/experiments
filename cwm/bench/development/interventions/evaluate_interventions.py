"""Score source interventions using raw V8 observations and the released predictors."""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import subprocess
import sys

from programs import cases

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "local_edit"))
from edit import Editor
from inference import generate
from model import TRAIN, examples, frame_row, prompt
from provenance import TRAIN_SHA
from score import grade

PAIRED_SHA = "3f6b05edf7710489610c0c9ad1cf4333817be4a4ef60282a17a0770e7f8b13c0"


def load_data(original):
    c2 = HERE.parent / "c2"
    tape = c2 / "probes/pauses.jsonl.gz" if original else HERE / "tape.jsonl.gz"
    digest = json.loads((c2 / "probe-pins.json").read_text())["pauses"] if original else PAIRED_SHA
    raw = gzip.decompress(tape.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == digest
    training_sources = {s for s, _, _ in examples(TRAIN, expected_sha=TRAIN_SHA)}
    runs = [json.loads(line) for line in raw.splitlines()]
    if not original:
        for (_, program), run in zip(cases(), runs, strict=True):
            assert {k: run[k] for k in program} == program
    rows = []
    for run in runs:
        entry, fn = run["entry"], run["fn"]
        source = run["files"][entry]
        assert source not in training_sources, "Held program occurs in the execution training tape"
        assert run["frames"][0]["stack"][0]["fn"] == ""
        frames = [frame_row(f, entry, fn) for f in run["frames"][1:]]
        assert len(frames) >= 2 and frames[-1].startswith("R,")
        rows.append(dict(source=source, args=run["args"], frames=frames))
    if not original:
        for a, b in zip(runs[::2], runs[1::2], strict=True):
            (current, left), (other, right) = a["frames"][1:3], b["frames"][1:3]
            assert current == other and a["files"] != b["files"]
            assert (left["kind"], left["stack"]) == (right["kind"], right["stack"])
            assert left["locals"] != right["locals"]
            assert all(n["locals"] != current["locals"] for n in (left, right))
    return tape, digest, runs, rows


def predict_structured(tape, runs, rows, original):
    outputs, trajectories = [], []
    mode = "trajectory" if original else "first"
    raw = subprocess.check_output(["bun", HERE / "structured.ts", mode, tape], text=True)
    for run, row, line in zip(runs, rows, raw.splitlines(), strict=True):
        reply = json.loads(line)
        assert (reply["entry"], reply["source"], reply["args"]) == (run["entry"], row["source"], run["args"])
        assert len(reply["next"]) == (len(row["frames"]) - 1 if original else 1)
        for frame in reply["next"]:
            text = frame_row(frame, run["entry"], run["fn"]) if frame and "stack" in frame else None
            outputs.append({"text": text, "stopped": text is not None})
        if original:
            prediction = [frame_row(f, run["entry"], run["fn"]) for f in reply["rollout"]]
            trajectories.append({**row, "predicted": prediction, "exact": prediction == row["frames"][1:]})
    return outputs, trajectories


def evaluate(arm, original):
    if original and arm != "structured":
        raise ValueError("The original MiniCPM5 trajectory results are archived under development/results")
    tape, digest, runs, rows = load_data(original)
    if arm == "structured":
        outputs, trajectories = predict_structured(tape, runs, rows, original)
    else:
        outputs, trajectories = [], []
        editor = Editor(arm)
        users = [prompt(r["source"], r["frames"][0]) for r in rows]
        for i in range(0, len(users), 6):
            outputs.extend(generate(editor.model, editor.tok, users[i:i+6], 32))

    examples_to_score = []
    for row in rows:
        frames = row["frames"] if original else row["frames"][:2]
        examples_to_score.extend((row, current, target) for current, target in zip(frames, frames[1:]))
    predictions = []
    totals = Counter()
    for (r, current, target), reply in zip(examples_to_score, outputs, strict=True):
        metrics = grade(current, target, (reply["text"] or "") if reply["stopped"] else "")
        totals.update(metrics)
        predictions.append(dict(source=r["source"], args=r["args"], current=current,
                                target=target, reply=reply, exact=bool(metrics["exact"])))
    if original:
        pairs = [(a, b) for (a, x), (b, y) in combinations(enumerate(predictions), 2)
                 if x["source"] != y["source"] and x["current"] == y["current"] and x["target"] != y["target"]]
    else:
        pairs = [(i, i+1) for i in range(0, len(rows), 2)]
    totals.update(pairs=len(pairs), both=sum(predictions[a]["exact"] and predictions[b]["exact"] for a, b in pairs))
    if original:
        totals.update(rollouts=len(trajectories), exact_rollouts=sum(r["exact"] for r in trajectories))
    return dict(arm=arm, reference_training_tape_sha256=TRAIN_SHA, held_tape_sha256=digest, metrics=totals,
                predictions=predictions, pair_indices=pairs, trajectories=trajectories)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("arm", choices=["base", "trained", "edit-only", "structured"])
    parser.add_argument("--original", action="store_true")
    args = parser.parse_args()
    print(json.dumps(evaluate(args.arm, args.original), separators=(",", ":")))
