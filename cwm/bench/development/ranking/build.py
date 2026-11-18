"""Build the reversal blocks from the frozen C2 oracle and original feature cache."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import torch
from encoder import ARMS, C2, Encoder, request

sys.path.insert(0, str(C2))
from data import ORACLE_SHA, corpus, digest, verified
from model import REVISION, target_ids

FROZEN = {
    "inputs": "702f266cf22a35e4c727069154591192a5fb9761c921ba4478e6af99a92df27b",
    "residuals": "a2c41c118448f480383c99dfb1d300a805ce0cb75e84397861f04218592cd456",
    "labels": "ffb56474c4d4eefac2c60dda1e085153843e36c06c92fbfd9e8405fb87d29635",
}


def episodes():
    data = verified(C2 / "data/oracle.jsonl.gz", ORACLE_SHA)
    records = []
    for ep in map(json.loads, data.splitlines()):
        writes = [dict(op="write", path=ep["path"], text=a["text"]) for a in ep["alternatives"]]
        value = {k: ep[k] for k in ("goal", "path", "files")}
        value["candidates"] = writes
        request(value)
        exits = [a["exit"] for a in ep["alternatives"]]
        assert sorted(exits) == [0, 1] and writes[0] != writes[1]
        records.append((ep["family"], ep["turn"], value, exits.index(0)))
    assert len(records) == 60
    assert len({r[0] for r in records}) == 10
    for a, b in zip(records[::2], records[1::2], strict=True):
        assert a[:2] == b[:2] and a[-1] != b[-1]
        assert a[2]["candidates"] == b[2]["candidates"] and a[2]["goal"] != b[2]["goal"]
    return records


@torch.inference_mode()
def archived(encoder, path):
    data = torch.load(path, weights_only=True)
    rows = corpus()
    if data["corpus"] != digest(rows) or data["revision"] != REVISION:
        raise ValueError("Changed C2 corpus or model")
    for name, sha in FROZEN.items():
        if hashlib.sha256(data[name].numpy().tobytes()).hexdigest() != sha:
            raise ValueError(f"Changed C2 frozen feature tensor {name}")
    at = 0
    index = {}
    for row in rows:
        suffix = target_ids(encoder.tok, row["target"])
        assert data["labels"][at:at+len(suffix)].tolist() == suffix
        if row["task"] == "forecast" and row["target"] in ("pass", "fail"):
            state = json.loads(row["prompt"].split("\n", 1)[1])
            goal = next(e["user"] for e in reversed(state["history"]) if "user" in e)
            key = row["family"], goal, state["candidate"]["text"]
            assert key not in index
            index[key] = {}
            for arm in encoder.arms:
                h = encoder.hidden(arm, data["inputs"][at], data["residuals"][at])
                index[key][arm] = dict(archived_final=h, archived_margin=encoder.margin(
                    h, encoder.pass_id, encoder.fail_id))
        at += len(suffix)
    assert at == len(data["labels"]) and len(index) == 120
    return index


def build(cache, out):
    records = episodes()
    encoder = Encoder(ARMS)
    history = archived(encoder, cache)
    blocks = []
    for i, (family, turn, value, choice) in enumerate(records):
        diff = encoder.difference(value, ablations=True)
        past = [history[family, value["goal"], w["text"]] for w in value["candidates"]]
        for arm in ARMS:
            for key in past[0][arm]:
                diff[arm][key] = past[0][arm][key] - past[1][arm][key]
        blocks.append(dict(family=family, turn=turn, choice=choice, features=diff))
        if (i+1) % 6 == 0:
            print(f"cached {i+1}/60 requests", flush=True)
    partial = out.with_suffix(".partial")
    torch.save(dict(schema=1, oracle=ORACLE_SHA, original=FROZEN, records=blocks), partial)
    partial.replace(out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("original", type=Path)
    p.add_argument("out", type=Path)
    args = p.parse_args()
    build(args.original, args.out)
