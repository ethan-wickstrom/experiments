"""Diagnostic only. Read visible requests plus externally supplied numeric spans."""
import json
import sys
from pathlib import Path
from time import monotonic

checkout, arm = sys.argv[1:3]
sys.path.insert(0, str(Path(checkout).resolve() / "cwm/bench/development/local_edit"))
from edit import Editor
from wire import inspect_request, splice, user

editor = Editor(arm)
assert editor.budget == 96
for line in sys.stdin:
    item = json.loads(line)
    assert set(item) == {"request", "span"}
    req, (start, end) = item["request"], item["span"]
    source = inspect_request(req)[req["path"]]
    prompt = user(req, (start, end))
    now = monotonic()
    replacement = editor.generate(prompt, editor.budget)
    elapsed = round(1000 * (monotonic() - now))
    response = dict(stopped=False, error="replacement token cap", start=start, end=end)
    if replacement is not None:
        response = dict(stopped=True, start=start, end=end, replacement=replacement,
                        text=splice(source, start, end, replacement))
    print(json.dumps(dict(prompt=prompt, response=response, elapsedMs=elapsed)), flush=True)
