"""Project JSONL is authored by the TS collector. Reuse the pinned debugger projection."""

import gzip
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "minicpm"))
from model import TRAIN, examples, prompt
from provenance import TRAIN_SHA

DATA = HERE / "data"
PROJECT_SHA = "ef845e3a376181ae0aafab3c93a09731c3391a0c4d9e8fd56c97d65bd3df0425"
ORACLE_SHA = "a80a2d8e956d37f9319be25d2543d0397972a3e9a1a1e852e8d2b3d5708058ff"
TRAINING_SHA = "c0f61edeeb8370079dedfafd3100b363a1e0bb4389558779c6b41d6372f23354"


def verified(path, expected):
    data = gzip.decompress(path.read_bytes())
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Changed tape: {path}")
    return data


def corpus():
    verified(DATA / "oracle.jsonl.gz", ORACLE_SHA)
    rows = list(map(json.loads, verified(DATA / "projects.jsonl.gz", PROJECT_SHA).splitlines()))
    for source, current, target in examples(TRAIN, expected_sha=TRAIN_SHA):
        family = "pause-" + hashlib.sha256(source.encode()).hexdigest()[:12]
        rows.append(dict(family=family, task="execution", prompt=prompt(source, current), target=target))
    if hashlib.sha256(canonical(rows)).hexdigest() != TRAINING_SHA:
        raise ValueError("Derived examples differ from the frozen training corpus")
    return rows


def canonical(rows):
    return "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows).encode()


if __name__ == "__main__":
    sys.stdout.buffer.write(canonical(corpus()))
