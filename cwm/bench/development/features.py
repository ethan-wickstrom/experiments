"""Build an FP32 target-position cache on the release checkpoint; no training here."""

import argparse
from collections import defaultdict
import hashlib
import json
import statistics
import time
from pathlib import Path

import torch

from corpus import HERE, canonical, corpus
from model import REVISION, chat_ids, load, target_ids

CACHE_VERSION = 1


@torch.inference_mode()
def build(out):
    rows = corpus()
    data_hash = hashlib.sha256(canonical(rows)).hexdigest()
    base, tok = load(verify_local=True)
    active = {}

    def capture(name):
        def hook(module, args):
            active[name] = args[0]
        return hook

    hooks = [
        base.model.layers[-1].mlp.down_proj.register_forward_pre_hook(capture("x")),
        base.model.norm.register_forward_pre_hook(capture("residual")),
    ]
    inputs, residuals, labels, tasks = [], [], [], []
    lengths = defaultdict(list)
    start = time.monotonic()
    try:
        for i, row in enumerate(rows):
            prefix = chat_ids(tok, row["prompt"])
            suffix = target_ids(tok, row["target"])
            length = len(prefix) + len(suffix)
            ids = torch.tensor([prefix + suffix[:-1]])
            base.model(input_ids=ids, use_cache=False)
            first = len(prefix) - 1
            inputs.append(active["x"][0, first:].clone())
            residuals.append(active["residual"][0, first:].clone())
            labels.extend(suffix)
            tasks.extend([row["task"]] * len(suffix))
            lengths[row["task"]].append([len(prefix),len(suffix),length])
            if (i + 1) % 25 == 0:
                print(f"cached {i+1}/{len(rows)} rows in {time.monotonic()-start:.1f}s", flush=True)
    finally:
        for hook in hooks:
            hook.remove()
    summary = {}
    for task, sizes in lengths.items():
        summary[task] = dict(records=len(sizes), target_tokens=sum(s[1] for s in sizes))
        for j, field in enumerate(("prompt", "target", "total")):
            values = [s[j] for s in sizes]
            summary[task][field] = dict(min=min(values), median=statistics.median(values), max=max(values))
    cache = dict(version=CACHE_VERSION, revision=REVISION, corpus=data_hash,
                 inputs=torch.cat(inputs), residuals=torch.cat(residuals), labels=torch.tensor(labels),
                 positions={task:torch.tensor([j for j,t in enumerate(tasks) if t == task]) for task in lengths},
                 lengths=summary)
    temp = out.with_suffix(".partial")
    torch.save(cache, temp)
    temp.replace(out)
    print(json.dumps(summary))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("output", type=Path)
    args = p.parse_args()
    if args.output.exists():
        p.error("Choose a fresh cache path")
    build(args.output)
