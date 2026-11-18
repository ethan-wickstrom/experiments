"""Evaluate the editing weights on the previously frozen consequence and next-pause tasks."""
import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path

import torch
from backbone import HERE, chat_ids
from edit import Editor
from evaluate import pause_score
from provenance import file_hash

REVERSALS = HERE.parent / "results/reversals.json.gz"
REVERSALS_SHA = "df0d076c179723632a80c8b610cfcbceb386ddf794c8499efc510ccde8c5349c"


@torch.inference_mode()
def margins(editor, prompts):
    positive, = editor.tok.encode("pass", add_special_tokens=False)
    negative, = editor.tok.encode("fail", add_special_tokens=False)
    scores = []
    for prompt in prompts:
        ids = chat_ids(editor.tok, prompt)
        logits = editor.model(input_ids=torch.tensor([ids]), use_cache=False, logits_to_keep=1).logits[0, -1]
        scores.append((logits[positive] - logits[negative]).item())
    return scores


def grade_reversals(rows, scores):
    pairs = defaultdict(list)
    label_hits = 0
    for row, score in zip(rows, scores, strict=True):
        passed = row["actual"]["exit"] == 0
        label_hits += score > 0 if passed else score < 0
        pairs[(row["name"], row["spec"])].append((passed, score))
    by_family = defaultdict(list)
    for (family, _), pair in pairs.items():
        assert len(pair) == 2 and {passed for passed, _ in pair} == {False, True}
        fail, success = sorted(pair)
        by_family[family].append(success[1] > fail[1])
    assert all(len(forks) == 2 for forks in by_family.values())
    return dict(correct_labels=label_hits, labels=len(rows),
                correct_choices=sum(sum(xs) for xs in by_family.values()), choices=len(pairs),
                correct_both=sum(all(xs) for xs in by_family.values()), families=len(by_family))


def evaluate(arm):
    if file_hash(REVERSALS) != REVERSALS_SHA:
        raise ValueError("Changed reversal corpus")
    with gzip.open(REVERSALS, "rt") as file:
        rows = json.load(file)
    editor = Editor(arm)
    scores = margins(editor, (row["forecast"] for row in rows))
    # The wrapped base shares the active LoRA modules in the last two decoder blocks.
    base = editor.model if arm == "base" else editor.model.get_base_model()
    with torch.inference_mode():
        execution = pause_score(editor.model, base, editor.tok)
    return dict(arm=arm, corpus_sha256=REVERSALS_SHA, margins=scores,
                ranking=grade_reversals(rows, scores), execution=execution)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("arm", choices=["base", "edit-only", "trained"])
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = evaluate(args.arm)
    with args.output.open("xb") as file:
        file.write(gzip.compress(json.dumps(report, separators=(",", ":")).encode(), mtime=0))
    print(args.arm, report["ranking"], report["execution"]["metrics"], flush=True)
