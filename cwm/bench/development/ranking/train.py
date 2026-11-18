"""Fit the predeclared readouts, holding out all turns and forks of each family."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import torch
from safetensors.torch import save_file

from build import FROZEN, ORACLE_SHA, episodes
from encoder import ARMS, WEIGHTS, HERE
from head import FULL, REGULARIZATION, TIE, score, train
from model import REVISION
from provenance import BASE_FILES, file_hash

ABLATIONS = {
    "archived_final": ("archived_final",),
    "last_final": ("last_final",),
    "first_final": ("first_final",),
    "first_token_evidence": ("first_goal_logp", "first_checks_logp"),
    "full": FULL,
}
RAW = ("archived_margin", "last_margin", "first_margin", "comparison", "first_goal_logp", "first_checks_logp")


def summarize(values, signs):
    margins = [m*s for m, s in zip(values, signs, strict=True)]
    correct = [m > TIE for m in margins]
    return dict(correct=sum(correct), ties=sum(abs(m) <= TIE for m in margins),
                both=sum(a and b for a, b in zip(correct[::2], correct[1::2], strict=True)),
                requests=len(correct), blocks=len(correct)//2)


def fit(cache, out):
    torch.set_num_threads(1)
    expected = (HERE / "features.sha256").read_text().split()[0]
    if file_hash(cache) != expected:
        raise ValueError("Ranking cache checksum mismatch")
    data = torch.load(cache, weights_only=True)
    if data["schema"] != 1 or data["oracle"] != ORACLE_SHA or data["original"] != FROZEN:
        raise ValueError("Unexpected ranker feature schema or source")
    records = data["records"]
    pairs = episodes()
    assert len(pairs) == len(records) and all(
        (f, t, choice) == (r["family"], r["turn"], r["choice"])
        for (f, t, _, choice), r in zip(pairs, records, strict=True))
    signs = [1 if r["choice"] == 0 else -1 for r in records]
    families = [r["family"] for r in records]
    assert len(set(families)) == 10 and all(families.count(f) == 6 for f in families)
    out.mkdir(parents=True, exist_ok=True)
    pins = dict(base_revision=REVISION, base=BASE_FILES, adapters=WEIGHTS, oracle=ORACLE_SHA,
                c2_features=FROZEN, features_sha256=file_hash(cache), regularization=REGULARIZATION,
                heads={}, protocol=file_hash(HERE / "protocol.md"),
                code={name: file_hash(HERE / name) for name in
                      ("encoder.py", "build.py", "head.py", "rank.py", "train.py")})
    report = {}
    rows = []
    # Fixed preference for one candidate, independent of the requirement.
    report["condition_blind"] = summarize([1.0] * len(records), signs)
    for arm in ARMS:
        features = [r["features"][arm] for r in records]
        outcomes = {key: [float(r[key]) for r in features] for key in RAW}
        for method, keys in ABLATIONS.items():
            held = [None] * len(signs)
            for family in sorted(set(families)):
                fit_idx = [i for i, f in enumerate(families) if f != family]
                head = train([features[i] for i in fit_idx], [signs[i] for i in fit_idx], keys)
                for i, f in enumerate(families):
                    if f == family:
                        held[i] = score(features[i], head)
            outcomes[method] = held
        report[arm] = {name: summarize(margins, signs) for name, margins in outcomes.items()}
        head = train(features, signs, FULL)
        weights = out / f"{arm}.safetensors"
        save_file(head, weights)
        pins["heads"][arm] = file_hash(weights)
        report[arm]["full_resubstitution"] = summarize([score(r, head) for r in features], signs)
        for i, (family, turn, value, choice) in enumerate(pairs):
            rows.append(dict(arm=arm, family=family, turn=turn, goal=value["goal"], observed_choice=choice,
                             margins={m: s[i] for m, s in outcomes.items()}))
    tape = "".join(json.dumps(row, separators=(",", ":"), allow_nan=False) + "\n" for row in rows).encode()
    (out / "fold-predictions.jsonl.gz").write_bytes(gzip.compress(tape, mtime=0))
    pins["fold_predictions_uncompressed"] = hashlib.sha256(tape).hexdigest()
    for name, document in [("diagnostics", report), ("provenance", pins)]:
        (out / f"{name}.json").write_text(json.dumps(document, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cache", type=Path)
    p.add_argument("out", type=Path)
    args = p.parse_args()
    fit(args.cache, args.out)
