"""Fit the matched B or C derivative. The cache contains frozen base activations only."""
import argparse
import hashlib
import json
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from torch.nn.functional import cross_entropy

from corpus import canonical, corpus
from features import CACHE_VERSION
from model import MODEL_ID, REVISION, chat_ids, load, target_ids

DRAWS = {"B": {"policy": 48}, "C": {"policy": 24, "execution": 12, "forecast": 12}}
STEPS = 256
SEED = 17


def train(args):
    rows = corpus()
    digest = hashlib.sha256(canonical(rows)).hexdigest()
    cache = torch.load(args.cache, weights_only=True, map_location="cpu")
    if (cache["version"], cache["revision"], cache["corpus"]) != (CACHE_VERSION, REVISION, digest):
        raise ValueError("Cache does not match pinned training corpus, release and feature schema")
    base, tok = load(verify_local=True)
    torch.manual_seed(SEED)
    config = LoraConfig(task_type="CAUSAL_LM", r=16, lora_alpha=16, lora_dropout=0.0,
                        target_modules=["model.layers.23.mlp.down_proj"], bias="none")
    model = get_peft_model(base, config)
    layer = base.model.layers[-1].mlp.down_proj
    a, b = layer.lora_A["default"], layer.lora_B["default"]
    params = [p for p in model.parameters() if p.requires_grad]
    assert sum(p.numel() for p in params) == 98304
    optimizer = torch.optim.AdamW(params, lr=0.001)
    sampler = torch.Generator().manual_seed(SEED)
    recipe = dict(arm=args.arm, revision=REVISION, corpus=digest, rank=16, alpha=16,
                  draws=DRAWS[args.arm], seed=SEED, lr=0.001, steps=STEPS, cache_version=CACHE_VERSION)
    out = args.out
    out.mkdir(parents=True, exist_ok=False)
    log = []

    def logits(idx):
        delta = b(a(cache["inputs"][idx])) * layer.scaling["default"]
        return base.lm_head(base.model.norm(cache["residuals"][idx] + delta))

    def update():
        parts = []
        for task, count in DRAWS[args.arm].items():
            pool = cache["positions"][task]
            parts.append(pool[torch.randint(len(pool), (count,), generator=sampler)])
        idx = torch.cat(parts)
        optimizer.zero_grad()
        loss = cross_entropy(logits(idx), cache["labels"][idx])
        loss.backward()
        optimizer.step()
        return idx, loss.item()

    def checkpoint(step):
        state = dict(step=step, recipe=recipe, a=a.state_dict(), b=b.state_dict(), log=log,
                     optimizer=optimizer.state_dict(), sampler=sampler.get_state(), rng=torch.get_rng_state())
        path = out / "state.partial"
        torch.save(state, path)
        path.replace(out / "state.pt")

    def restore(path):
        state = torch.load(path, weights_only=True)
        if state["recipe"] != recipe:
            raise ValueError("Checkpoint recipe mismatch")
        a.load_state_dict(state["a"])
        b.load_state_dict(state["b"])
        optimizer.load_state_dict(state["optimizer"])
        sampler.set_state(state["sampler"])
        torch.set_rng_state(state["rng"])
        return state["step"], state["log"]

    initial_step = 0
    if args.resume:
        initial_step, log = restore(args.resume)
    if not 0 <= initial_step < args.stop_at <= STEPS:
        raise ValueError("Stop step must follow checkpoint and be within the frozen schedule")
    for step in range(initial_step + 1, args.stop_at + 1):
        if step == 129:
            # Compare the actual next update (including Adam moments) with a
            # restarted update from disk at step 128. Continue along the restarted path.
            if initial_step == 128:
                checkpoint(128)
            idx_a, loss_a = update()
            first_a, first_b = a.weight.detach().clone(), b.weight.detach().clone()
            restore(out / "state.pt")
            idx, loss = update()
            assert loss == loss_a and torch.equal(idx_a, idx)
            assert torch.equal(a.weight, first_a) and torch.equal(b.weight, first_b)
        else:
            _, loss = update()
        if step % 32 == 0 or step == args.stop_at:
            log.append({"step":step, "batch_ce":loss})
            print(args.arm, step, round(loss, 5), flush=True)
            checkpoint(step)
    assert torch.count_nonzero(b.weight).item() > 0
    with torch.no_grad():
        first = rows[0]
        prefix = chat_ids(tok, first["prompt"])
        suffix = target_ids(tok, first["target"])
        ids = torch.tensor([prefix + suffix[:-1]])
        full = model(input_ids=ids, use_cache=False).logits[0, len(prefix)-1:]
        torch.testing.assert_close(full, logits(slice(0,len(suffix))), atol=3e-4, rtol=1e-4)
    config.base_model_name_or_path, config.revision = MODEL_ID, REVISION
    model.save_pretrained(out / "peft", save_embedding_layers=False)
    (out / "peft/README.md").unlink(missing_ok=True)
    report = dict(recipe=recipe, step=args.stop_at, data_lengths=cache["lengths"], history=log)
    (out / "fit.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--arm", choices=("B","C"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--stop-at", type=int, default=STEPS)
    train(parser.parse_args())
