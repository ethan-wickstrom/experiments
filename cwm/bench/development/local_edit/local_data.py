"""Training views and mechanically derived edit targets from verified episodes."""
import hashlib
import json

from backbone import C2, HERE, corpus
from data import ORACLE_SHA, verified
from wire import derive, user

TRAIN = "926eac2be9ae6e2f6023cc4d19ff6ec1f12d57b4e7ff30058bc25581d78763c0"
HOLDOUT = "c6a9ad36e6471dfdfe801213cb16e73a8956bb0963ba55cbf490e69eb3caa51a"


def authored(split):
    digest = {"train": TRAIN, "holdout": HOLDOUT}[split]
    raw = verified(HERE / f"data/{split}.jsonl.gz", digest)
    for line in raw.splitlines():
        ep = json.loads(line)
        assert ep["split"] == split and [ep[k]["exit"] for k in
            ("observed_before","observed_after","observed_extra")] == [1,0,0]
        files = [{"path": ep["path"], "text": ep["before"]}, {"path": "checks.test.ts", "text":ep["check"]}]
        req = dict(goal=ep["goal"], path=ep["path"], files=files)
        if ep["show_observed"]:
            diag = [s for s in ep["observed_before"]["stderr"].splitlines() if s.startswith(("Expected:", "Received:"))]
            req["observed"] = "fail" + ("\n" + "\n".join(diag)[:240] if diag else "")
        yield ep, req


def edit_rows(family, req, before, after):
    start, end, replacement = derive(before, after)
    return [dict(family=family, task="locate", prompt=user(req), target=f"{start}:{end}"),
            dict(family=family, task="fill", prompt=user(req, (start, end)), target=replacement)]


def training():
    rows = []
    for ep, req in authored("train"):
        rows.extend(edit_rows(ep["family"], req, ep["before"], ep["after"]))
    for line in verified(C2 / "data/oracle.jsonl.gz", ORACLE_SHA).splitlines():
        ep = json.loads(line)
        req = {k: ep[k] for k in ("goal", "path", "files")}
        assert ep["before"]["exit"] and not ep["after"]["exit"]
        rows.extend(edit_rows(ep["family"], req, ep["before"]["text"], ep["after"]["text"]))
    rows.extend(r for r in corpus() if r["task"] in ("forecast", "execution"))
    return rows


def digest(rows):
    return hashlib.sha256("".join(json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n"
                                  for r in rows).encode()).hexdigest()
