"""Paired greedy next-pause and teacher-forced full-vocabulary log loss."""

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import torch
from torch.nn.functional import cross_entropy

from model import (
    ADAPTER, TRAIN, adapted, chat_ids, examples, generate, load, prompt, target_ids,
)


@torch.no_grad()
def token_loss(base, tok, rows):
    # Right-pad whole sequences, then apply the untied 130560-way language head
    # only where target tokens are scored, including the answer terminator.
    sequences, target_tokens, positions = [], [], []
    for index, (source, current, target) in enumerate(rows):
        prefix = chat_ids(tok, prompt(source, current))
        suffix = target_ids(tok, target)
        sequences.append(prefix + suffix[:-1])
        positions.extend((index, len(prefix) - 1 + i) for i in range(len(suffix)))
        target_tokens.extend(suffix)
    width = max(map(len, sequences))
    ids = torch.tensor([s + [tok.pad_token_id] * (width - len(s)) for s in sequences])
    mask = torch.tensor([[1] * len(s) + [0] * (width - len(s)) for s in sequences])
    hidden = base.model(input_ids=ids, attention_mask=mask, use_cache=False).last_hidden_state
    batch_indices, time_indices = zip(*positions)
    logits = base.lm_head(hidden[list(batch_indices), list(time_indices)])
    total = cross_entropy(logits, torch.tensor(target_tokens), reduction="sum").item()
    return total, len(target_tokens)


def grade(current, target, output):
    gold = target.split(",")
    changed = gold[3:5] != current.split(",")[3:5]
    fields = output.split(",")
    valid = len(fields) in (5, 6) and fields[0] == ("S" if len(fields) == 5 else "R")
    valid = valid and all(re.fullmatch(r"-?(0|[1-9][0-9]*)", v) for v in fields[1:])
    exact = output == target
    return dict(rows=1, exact=int(exact), valid=int(valid),
                site_event=int(valid and gold[:3] == fields[:3]),
                locals=int(valid and gold[3:5] == fields[3:5]), changed=int(changed),
                changed_locals_correct=int(changed and valid and gold[3:5] == fields[3:5]),
                changed_exact=int(changed and exact))


def run(model, base, tok, rows):
    nll, token_count = 0.0, 0
    totals, by_source, outputs = Counter(), {}, []
    for i in range(0, len(rows), 6):
        batch = rows[i:i + 6]
        users = [prompt(source, current) for source, current, _ in batch]
        texts = generate(model, tok, users, limit=32)
        batch_nll, batch_tokens = token_loss(base, tok, batch)
        nll += batch_nll
        token_count += batch_tokens
        for (source, current, target), text in zip(batch, texts, strict=True):
            key = hashlib.sha256(source.encode()).hexdigest()[:12]
            counts = grade(current, target, text)
            totals.update(counts)
            by_source.setdefault(key, Counter()).update(counts)
            outputs.append(dict(source=key, current=current, expected=target, generated=text))
    return dict(counts=totals, target_tokens=token_count, nll=nll / token_count,
                by_source=by_source, predictions=outputs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", type=Path)
    parser.add_argument("--adapter", type=Path, default=ADAPTER)
    args = parser.parse_args()
    rows = examples(args.traces)
    if not rows or {r[0] for r in rows} & {r[0] for r in examples(TRAIN)}:
        parser.error("Evaluation requires source-disjoint nonempty observations")
    base, tok = load()
    result = {"base": run(base, base, tok, rows)}
    model = adapted(base, args.adapter)
    result["adapted"] = run(model, base, tok, rows)
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
