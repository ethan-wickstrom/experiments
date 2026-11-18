"""Can the locator reverse its preference between identical spans when source moves?"""
import argparse
import gzip
import json
from pathlib import Path

from likelihood import sequence_logprobs
from edit import Editor
from local_data import HOLDOUT, authored
from wire import derive, splice, user


def evaluate(arm):
    editor = Editor(arm)
    records = []
    for episode, request in authored("holdout"):
        before, after = episode["before"], episode["after"]
        eol = "\r\n" if "\r\n" in before else "\n"
        trivia = "// Module notes" + eol + "// End notes" + eol
        assert before.endswith(eol) and after.endswith(eol)
        start, end, replacement = derive(before, after)
        spans = [(start, end), (start + 2, end + 2)]
        scores = []
        for index, (source, reference) in enumerate(((before + trivia, after + trivia),
                                                     (trivia + before, trivia + after))):
            assert splice(source, *spans[index], replacement) == reference
            files = [{**f, "text": source} if f["path"] == request["path"] else f for f in request["files"]]
            scores.append(sequence_logprobs(editor, user({**request, "files": files}), [f"{a}:{b}" for a,b in spans]))
        hits = [pair[i] > pair[1-i] for i, pair in enumerate(scores)]
        records.append(dict(family=episode["family"], goal=episode["goal"], spans=spans, scores=scores, hits=hits))
    return dict(arm=arm, corpus_sha256=HOLDOUT, decisions=2*len(records), pairs=len(records),
                correct=sum(sum(r["hits"]) for r in records), both=sum(all(r["hits"]) for r in records),
                records=records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("arm", choices=["base", "edit-only", "trained"])
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = evaluate(args.arm)
    with args.output.open("xb") as file:
        file.write(gzip.compress(json.dumps(report, separators=(",", ":")).encode(), mtime=0))
    print({k: v for k, v in report.items() if k != "records"})
