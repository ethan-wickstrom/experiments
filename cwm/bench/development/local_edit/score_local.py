"""Apply the same learned-location protocol to both arms on frozen local families."""
import argparse
import json
from collections import Counter

from edit import Editor
from evaluate import run_tests
from local_data import authored
from wire import derive, lines


def evaluate(arm):
    editor = Editor(arm)
    outputs = []
    counts = {k:Counter() for k in ("all", "settings", "behavior")}
    for ep, request in authored("holdout"):
        start, end, replacement = derive(ep["before"], ep["after"])
        answer = editor(request)
        key = "settings" if ep["goal"].startswith("Set ") else "behavior"
        result = dict(family=ep["family"], goal=ep["goal"], kind=key, prediction=answer,
                      target=dict(start=start,end=end,replacement=replacement))
        metrics = dict(rows=1, located=(answer.get("start"),answer.get("end"))==(start,end),
                       stopped=answer["stopped"], exact=False, visible=False, both=False)
        if answer["stopped"]:
            text = answer["text"]
            original = lines(ep["before"])
            left, right = "".join(original[:answer["start"]]), "".join(original[answer["end"]:])
            assert text == left + answer["replacement"] + right
            result["visible"] = run_tests(request, text)
            result["extra"] = run_tests(request, text, ep["extra"])
            metrics.update(exact=text==ep["after"], visible=result["visible"]["passed"],
                           both=result["visible"]["passed"] and result["extra"]["passed"])
        counts["all"].update(metrics)
        counts[key].update(metrics)
        outputs.append(result)
    return dict(arm=arm, metrics=counts, outputs=outputs)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("arm", choices=["base","trained"])
    print(json.dumps(evaluate(p.parse_args().arm), separators=(",", ":")))
