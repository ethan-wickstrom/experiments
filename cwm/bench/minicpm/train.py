"""CPU LoRA fitting with an exact frozen-prefix cache for supervised target tokens."""

import argparse
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from torch.nn.functional import cross_entropy

from model import ADAPTER, MODEL_ID, REVISION, TRAIN, chat_ids, examples, load, prompt, target_ids
from provenance import TRAIN_SHA


def encode_example(tok, row):
    source, current, target = row
    prefix = chat_ids(tok, prompt(source, current))
    suffix = target_ids(tok, target)
    ids = torch.tensor([prefix + suffix[:-1]])
    return ids, len(prefix) - 1, torch.tensor(suffix)


@torch.no_grad()
def cache_targets(base, tok, rows):
    # Residual just before the final norm includes the base down projection.
    active = {}
    def capture(key):
        def hook(module, args):
            active[key] = args[0]
        return hook
    down = base.model.layers[-1].mlp.down_proj
    down_hook = down.register_forward_pre_hook(capture("features"))
    norm_hook = base.model.norm.register_forward_pre_hook(capture("residual"))
    features, residuals, labels = [], [], []
    try:
        for row in rows:
            ids, start, targets = encode_example(tok, row)
            base.model(input_ids=ids, use_cache=False)
            features.append(active["features"][0, start:].clone())
            residuals.append(active["residual"][0, start:].clone())
            labels.append(targets)
    finally:
        down_hook.remove()
        norm_hook.remove()
    return torch.cat(features), torch.cat(residuals), torch.cat(labels)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=ADAPTER, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("--out must be a fresh path")
    rows = examples(TRAIN, expected_sha=TRAIN_SHA)
    base, tok = load(verify_local=True)
    torch.manual_seed(17)
    features, residuals, labels = cache_targets(base, tok, rows)
    print(f"Cached {len(labels)} target positions from {len(rows)} transitions", flush=True)
    config = LoraConfig(
        task_type="CAUSAL_LM", r=8, lora_alpha=8, lora_dropout=0.0,
        target_modules=["model.layers.23.mlp.down_proj"], bias="none",
    )
    model = get_peft_model(base, config)
    layer = base.model.layers[-1].mlp.down_proj
    a, b = layer.lora_A["default"], layer.lora_B["default"]

    def logits(idx):
        delta = b(a(features[idx])) * layer.scaling["default"]
        return base.lm_head(base.model.norm(residuals[idx] + delta))

    params = [p for p in model.parameters() if p.requires_grad]
    assert sum(p.numel() for p in params) == 49152
    sampler = torch.Generator().manual_seed(17)
    optimizer = torch.optim.AdamW(params, lr=0.001)
    for step in range(160):
        idx = torch.randint(len(labels), (32,), generator=sampler)
        optimizer.zero_grad()
        loss = cross_entropy(logits(idx), labels[idx])
        loss.backward()
        optimizer.step()
        if (step + 1) % 40 == 0:
            print(f"update {step + 1}, batch CE {loss.item():.4f}", flush=True)
    # Compare cached training computation with the live adapter at every target
    # position of a complete training transition, including its end token.
    with torch.no_grad():
        ids, start, first_labels = encode_example(tok, rows[0])
        full = model(input_ids=ids, use_cache=False).logits[0, start:]
        torch.testing.assert_close(full, logits(slice(0, len(first_labels))), atol=3e-4, rtol=1e-4)
    config.base_model_name_or_path, config.revision = MODEL_ID, REVISION
    model.save_pretrained(args.out, save_embedding_layers=False)
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
