"""Retrospective source interventions on shared current pauses with different successors."""
import argparse
import gzip
from itertools import combinations
import json
from pathlib import Path

from backbone import C2
from edit import Editor
from likelihood import sequence_logprobs
from model import examples, prompt


def evaluate(arm):
    sha = json.loads((C2 / "probe-pins.json").read_text())["pauses"]
    observations = examples(C2 / "probes/pauses.jsonl.gz", expected_sha=sha)
    editor = Editor(arm)
    records = []
    for (left, current, a), (right, other, b) in combinations(observations, 2):
        if current != other or a == b or left == right:
            continue
        scores = [sequence_logprobs(editor, prompt(source, current), [a, b])
                  for source in (left, right)]
        records.append(dict(current=current, sources=[left, right], alternatives=[a, b],
                            scores=scores, correct=[scores[0][0] > scores[0][1], scores[1][1] > scores[1][0]]))
    return dict(arm=arm, corpus_sha256=sha, pairs=len(records),
                both=sum(all(r["correct"]) for r in records), records=records)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("arm", choices=["base", "trained", "edit-only"])
    p.add_argument("output", type=Path)
    args = p.parse_args()
    report = evaluate(args.arm)
    with args.output.open("xb") as file:
        file.write(gzip.compress(json.dumps(report, separators=(",", ":")).encode(), mtime=0))
    print(args.arm, report["both"], "/", report["pairs"])
