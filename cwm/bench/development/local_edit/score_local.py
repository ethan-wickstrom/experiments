"""Apply the same learned-location protocol to all arms on frozen local families."""
import argparse
import json
from collections import Counter

from edit import Editor
from evaluate import run_tests
from local_data import authored
from wire import derive, lines


def summarize(outputs):
    counts = {k:Counter() for k in ("all", "settings", "behavior")}
    for row in outputs:
        answer, target = row["prediction"], row["target"]
        visible = row.get("visible", {}).get("passed", False)
        extra = row.get("extra", {}).get("passed", False)
        located = (answer.get("start"), answer.get("end")) == (target["start"], target["end"])
        metrics = dict(rows=1, stopped=answer["stopped"], located=located,
                       exact=row["exact"], visible=visible, extra=extra, both=visible and extra)
        counts["all"].update(metrics)
        counts[row["kind"]].update(metrics)
    return counts


def evaluate(arm):
    editor = Editor(arm)
    outputs = []
    for ep, request in authored("holdout"):
        start, end, replacement = derive(ep["before"], ep["after"])
        answer = editor(request)
        key = "settings" if ep["goal"].startswith("Set ") else "behavior"
        result = dict(family=ep["family"], goal=ep["goal"], kind=key, prediction=answer,
                      target=dict(start=start,end=end,replacement=replacement))
        result["exact"] = answer["stopped"] and answer["text"] == ep["after"]
        if answer["stopped"]:
            text = answer["text"]
            original = lines(ep["before"])
            left, right = "".join(original[:answer["start"]]), "".join(original[answer["end"]:])
            assert text == left + answer["replacement"] + right
            result["visible"] = run_tests(request, text)
            result["extra"] = run_tests(request, text, ep["extra"])
        outputs.append(result)
    return dict(arm=arm, metrics=summarize(outputs), outputs=outputs)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("arm", choices=["base","trained","edit-only"])
    print(json.dumps(evaluate(p.parse_args().arm), separators=(",", ":")))
