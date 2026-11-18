"""Build target-position features using a reusable causal KV prefix across neighbors."""
import argparse
import json
import time
from collections import defaultdict
from pathlib import Path
from statistics import median

import torch
from data import corpus, digest, encode
from model import REVISION, load


@torch.inference_mode()
def build(out):
    rows = corpus()
    base, tok = load()
    encoded = [encode(tok, row) for row in rows]
    live = {}
    def capture(key):
        def hook(module, args):
            live[key] = args[0]
        return hook

    handles = [
        base.model.layers[-1].mlp.down_proj.register_forward_pre_hook(capture("inputs")),
        base.model.norm.register_forward_pre_hook(capture("residuals")),
    ]
    features = {}
    previous = []
    kv = None
    pools = defaultdict(list)
    lengths = defaultdict(list)
    start = time.monotonic()
    try:
        for n, i in enumerate(sorted(range(len(rows)), key=lambda i: encoded[i][0])):
            prefix, suffix = encoded[i]
            ids = prefix + suffix[:-1]
            shared = 0
            while (shared < min(len(previous), len(prefix)-1) and ids[shared] == previous[shared]):
                shared += 1
            if kv is not None:
                kv.crop(shared)
            kv = base.model(input_ids=torch.tensor([ids[shared:]]),
                            past_key_values=kv, use_cache=True).past_key_values
            first = len(prefix)-1-shared
            features[i] = {key:value[0,first:].clone() for key,value in live.items()}
            previous = ids
            if n % 50 == 0:
                print(f"cached {n+1}/{len(rows)} rows in {time.monotonic()-start:.0f}s", flush=True)
        # Compare cached and ordinary uncached features on the longest forecast.
        i = max(range(len(rows)), key=lambda i:len(encoded[i][0]))
        prefix, suffix = encoded[i]
        base.model(input_ids=torch.tensor([prefix + suffix[:-1]]), use_cache=False)
        for key,value in live.items():
            torch.testing.assert_close(features[i][key], value[0,len(prefix)-1:], atol=2e-4, rtol=2e-4)
    finally:
        for handle in handles:
            handle.remove()
    labels=[]
    for i,row in enumerate(rows):
        prefix,suffix = encoded[i]
        task = row["task"]
        size = len(suffix)
        if task == "forecast":
            pool = "forecast_" + row["target"]
            pools[pool].extend(range(len(labels),len(labels)+size-1))
        else:
            pools[task].extend(range(len(labels),len(labels)+size))
        labels.extend(suffix)
        lengths[task].append((len(prefix),size,len(prefix)+size))
    report = {}
    for task, values in lengths.items():
        report[task] = {"records":len(values),"target_tokens":sum(v[1] for v in values)}
        for j,key in enumerate(["prompt","target","total"]):
            sizes=[v[j] for v in values]
            report[task][key]=[min(sizes),median(sizes),max(sizes)]
    obj={key:torch.cat([features[i][key] for i in range(len(rows))]) for key in live}
    obj.update(version=1,revision=REVISION,corpus=digest(rows),labels=torch.tensor(labels),
               positions={k:torch.tensor(v) for k,v in pools.items()},lengths=report)
    tmp=out.with_suffix(".partial")
    torch.save(obj,tmp)
    tmp.rename(out)
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("output",type=Path)
    args=p.parse_args()
    if args.output.exists():
        p.error("choose a fresh cache path")
    build(args.output)
