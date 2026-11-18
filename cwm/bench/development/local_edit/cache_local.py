"""Cache causal inputs to layer 22 on the verified training rows only."""
import argparse
import time
from pathlib import Path

import torch
from backbone import REVISION, load, top_logits
from data import encode
from local_data import digest, training

BLOCKS = 2


@torch.inference_mode()
def cache(out):
    rows = training()
    model, tokenizer = load()
    pairs = [encode(tokenizer, r) for r in rows]
    tasks = sorted({r["task"] for r in rows})
    lengths = {t: max(len(a)+len(b) for (a,b),r in zip(pairs, rows) if r["task"]==t) for t in tasks}
    print("max sequence length", lengths, flush=True)
    live = {}
    def remember(_module, args):
        live["hidden"] = args[0][0]
    hook = model.model.layers[-BLOCKS].register_forward_pre_hook(remember)
    kv = None
    previous = []
    previous_hidden = torch.empty((0, model.config.hidden_size))
    features = [None] * len(rows)
    start = time.monotonic()
    try:
        for n, i in enumerate(sorted(range(len(rows)), key=lambda i: pairs[i][0])):
            prefix, suffix = pairs[i]
            ids = prefix + suffix[:-1]
            shared = 0
            while shared < min(len(previous), len(prefix)-1) and ids[shared] == previous[shared]:
                shared += 1
            if kv is not None:
                kv.crop(shared)
            kv = model.model(input_ids=torch.tensor([ids[shared:]]), past_key_values=kv, use_cache=True).past_key_values
            hidden = torch.cat((previous_hidden[:shared], live["hidden"]))
            features[i] = dict(hidden=hidden, labels=torch.tensor(suffix), first=len(prefix)-1)
            previous, previous_hidden = ids, hidden
            if (n+1) % 50 == 0:
                print(n+1, "rows", round(time.monotonic()-start), "seconds", flush=True)
    finally:
        hook.remove()
    for task in tasks:
        i = next(i for i,r in enumerate(rows) if r["task"] == task)
        prefix, suffix = pairs[i]
        f = features[i]
        positions = torch.arange(f["first"], len(f["hidden"]))
        live = model(input_ids=torch.tensor([prefix+suffix[:-1]]),use_cache=False).logits[0,len(prefix)-1:]
        cached = top_logits(model, f["hidden"], positions, BLOCKS)
        torch.testing.assert_close(cached, live, atol=7e-4, rtol=2e-4)
    tmp = out.with_suffix(".partial")
    torch.save(dict(revision=REVISION, corpus=digest(rows), blocks=BLOCKS, rows=features), tmp)
    tmp.replace(out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("out",type=Path)
    cache(p.parse_args().out)
