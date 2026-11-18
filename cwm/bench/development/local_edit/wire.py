"""Public, byte-preserving localized edit protocol."""
import json
import re

LOCATE = ("Choose the contiguous lines to replace in the selected TypeScript file. "
          "Reply with start:end using zero-based half-open line boundaries.")
FILL = ("Write only the replacement TypeScript lines for the selected span. "
        "Preserve indentation and final line endings.")


def lines(text):
    parts = text.split("\n")
    return [s + "\n" for s in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def splice(text, start, end, replacement):
    parts = lines(text)
    if not (type(start) is int and type(end) is int and 0 <= start <= end <= len(parts)):
        raise ValueError("Invalid line span")
    return "".join(parts[:start]) + replacement + "".join(parts[end:])


def derive(before, after):
    a, b = lines(before), lines(after)
    start = 0
    while start < min(len(a), len(b)) and a[start] == b[start]:
        start += 1
    i, j = len(a), len(b)
    while i > start and j > start and a[i-1] == b[j-1]:
        i -= 1
        j -= 1
    replacement = "".join(b[start:j])
    assert splice(before, start, i, replacement) == after
    return start, i, replacement


def inspect_request(value):
    if not isinstance(value, dict) or not {"goal", "path", "files"} <= set(value) <= {"goal", "path", "files", "observed"}:
        raise ValueError("Expected goal, path, visible files and optional observed text")
    for key in ("goal", "path", "observed"):
        if key in value and not isinstance(value[key], str):
            raise ValueError(f"Expected string {key}")
    files = value["files"]
    if not isinstance(files, list) or not all(isinstance(f, dict) and set(f) == {"path", "text"} and
        isinstance(f["path"], str) and isinstance(f["text"], str) for f in files):
        raise ValueError("Expected path/text files")
    by_path = {f["path"]: f["text"] for f in files}
    if len(by_path) != len(files) or value["path"] not in by_path:
        raise ValueError("Expected unique visible files including the selected path")
    return by_path


def user(value, span=None):
    by_path = inspect_request(value)
    path = value["path"]
    state = dict(goal=value["goal"], path=path, lines=list(enumerate(lines(by_path.pop(path)))),
                 files=[{"path": k, "text": by_path[k]} for k in
                        sorted(by_path, key=lambda k: k.encode("utf-16-be", errors="surrogatepass"))])
    if "observed" in value:
        state["observed"] = value["observed"]
    if span is not None:
        state["span"] = list(span)
    serialized = json.dumps(state, separators=(",", ":"), ensure_ascii=False).replace("<", "\\u003c")
    serialized = re.sub(r"[\ud800-\udfff]", lambda m: "\\u%04x" % ord(m[0]), serialized)
    return (LOCATE if span is None else FILL) + "\n" + re.sub(r"/(?=(?:no_)?think)", lambda _: "\\u002f", serialized)
