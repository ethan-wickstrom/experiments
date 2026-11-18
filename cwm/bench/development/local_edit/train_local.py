"""Fit attention/MLP LoRA on exact frozen-prefix replay and export standard PEFT."""
import argparse
import hashlib
import json
import math
import random
import time
from collections import defaultdict
from pathlib import Path

import torch
import torch.nn.functional as F
from backbone import MODEL_ID, REVISION, adapt, load, top_logits
from cache_local import BLOCKS
from data import encode
from local_data import digest, training
from provenance import file_hash

SEED = 29
STEPS = 2048
CORPUS = "40aa5b7f1138fcd6890629483c5908ad0ce2ab71b1f3a55c99b18c62e87b1587"


def schedule(rows):
    rng = random.Random(SEED)
    pools = defaultdict(list)
    for i, r in enumerate(rows):
        pools[r["task"]].append(i)
    decks = defaultdict(list)
    plan = []
    for _ in range(STEPS // 16):
        tasks = ["locate"]*6 + ["fill"]*8 + ["forecast", "execution"]
        rng.shuffle(tasks)
        for task in tasks:
            if not decks[task]:
                decks[task] = pools[task].copy()
                rng.shuffle(decks[task])
            plan.append(decks[task].pop())
    return plan


def learning_rate(step):
    if step <= 64:
        return 0.0004 * step / 64
    phase = (step-64) / (STEPS-64)
    return 0.00008 + 0.00016 * (1+math.cos(math.pi*phase))


def fit(cache_path, out, checkpoint=None, arm="trained"):
    examples = training()
    data = torch.load(cache_path, weights_only=True)
    if (data["blocks"], data["revision"], data["corpus"], digest(examples)) != (BLOCKS, REVISION, CORPUS, CORPUS):
        raise ValueError("Wrong frozen corpus, feature depth or base")
    cache_sha = file_hash(cache_path)
    torch.manual_seed(SEED)
    base, tok = load()
    model = adapt(base, BLOCKS)
    params = {k:p for k,p in model.named_parameters() if p.requires_grad}
    assert sum(p.numel() for p in params.values()) == 1081344
    initial = hashlib.sha256()
    for name, p in sorted(params.items()):
        initial.update(name.encode())
        initial.update(p.detach().numpy().tobytes())
    colon, = tok.encode(":", add_special_tokens=False)
    stop = tok.convert_tokens_to_ids("<|im_end|>")
    optimizer = torch.optim.AdamW(params.values(), lr=0.0004)
    plan = schedule(examples)
    initial_step = 0
    history = []
    if checkpoint and checkpoint.exists():
        saved = torch.load(checkpoint, weights_only=True)
        if (saved["arm"], saved["corpus"], saved["cache_sha"], saved["plan"]) != (arm, CORPUS, cache_sha, plan):
            raise ValueError("Resume recipe mismatch")
        with torch.no_grad():
            for name, p in params.items():
                p.copy_(saved["weights"][name])
        optimizer.load_state_dict(saved["optimizer"])
        torch.set_rng_state(saved["rng"])
        initial_step, history = saved["step"], saved["history"]
    rows = data["rows"]
    assert len(rows) == len(examples)
    totals = defaultdict(list)
    started = time.monotonic()
    for step in range(initial_step+1, STEPS+1):
        i = plan[step-1]
        f, task = rows[i], examples[i]["task"]
        labels = f["labels"]
        pos = torch.arange(f["first"], len(f["hidden"]))
        assert len(labels) == len(pos)
        optimizer.param_groups[0]["lr"] = learning_rate(step)
        if arm == "trained" or task in ("locate", "fill"):
            optimizer.zero_grad()
            logits = top_logits(base, f["hidden"], pos, BLOCKS)
            losses = F.cross_entropy(logits, labels, reduction="none")
            if task == "locate":
                weights = torch.where((labels == colon) | (labels == stop), 0.25, 1.0)
                loss = (losses * weights).sum() / weights.sum()
            else:
                loss = losses.mean()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params.values(), 1.0)
            optimizer.step()
            totals[task].append(float(loss.detach()))
        if step % 128 == 0:
            summary = {k:sum(v)/len(v) for k,v in totals.items()}
            history.append(dict(step=step, mean_loss=summary))
            print(step, {k:round(v,3) for k,v in summary.items()}, round(time.monotonic()-started), flush=True)
            totals.clear()
        if checkpoint and step % 256 == 0:
            tmp = checkpoint.with_suffix(".partial")
            torch.save(dict(arm=arm, step=step, weights={k:p.detach() for k,p in params.items()},
                       optimizer=optimizer.state_dict(), rng=torch.get_rng_state(), corpus=CORPUS, cache_sha=cache_sha,
                       plan=plan, history=history), tmp)
            tmp.replace(checkpoint)
    with torch.no_grad():
        for task in ("locate", "fill", "forecast", "execution"):
            i = next(i for i,r in enumerate(examples) if r["task"]==task)
            prefix, suffix = encode(tok, examples[i])
            full = model(input_ids=torch.tensor([prefix+suffix[:-1]]), use_cache=False).logits[0,len(prefix)-1:]
            f = rows[i]
            cached = top_logits(base, f["hidden"], torch.arange(f["first"],len(f["hidden"])), BLOCKS)
            torch.testing.assert_close(cached, full, atol=1.5e-3, rtol=3e-4)
    out.mkdir(parents=True, exist_ok=True)
    config = model.peft_config["default"]
    config.base_model_name_or_path, config.revision = MODEL_ID, REVISION
    model.save_pretrained(out/"peft", save_embedding_layers=False)
    (out/"peft/README.md").unlink(missing_ok=True)
    edit_plan = [(s,i) for s,i in enumerate(plan, 1) if examples[i]["task"] in ("locate","fill")]
    report = dict(arm=arm, revision=REVISION, seed=SEED, steps=STEPS, blocks=BLOCKS, coefficients=1081344,
                  optimizer_steps=STEPS if arm=="trained" else len(edit_plan),
                  initial_sha256=initial.hexdigest(),
                  edit_plan_sha256=hashlib.sha256(json.dumps(edit_plan,separators=(",",":")).encode()).hexdigest(),
                  corpus=CORPUS, cache_sha256=cache_sha, peft_sha256=file_hash(out/"peft/adapter_model.safetensors"),
                  history=history)
    (out/"fit.json").write_text(json.dumps(report, indent=2)+"\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cache", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--arm", choices=["trained","edit-only"], default="trained")
    p.add_argument("--checkpoint", type=Path)
    a = p.parse_args()
    fit(a.cache, a.out, a.checkpoint, a.arm)
