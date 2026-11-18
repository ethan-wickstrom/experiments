"""Measure the cost of a real CPU training step before freezing top-block depth."""
import json
import statistics
import time

import torch
from backbone import adapt, corpus, chat_ids, load, target_ids, top_logits


def benchmark():
    row = next(r for r in corpus() if r["task"] == "source")
    results = []
    for count in [0, 1, 2]:
        torch.manual_seed(29)
        base, tok = load()
        prefix, suffix = chat_ids(tok, row["prompt"]), target_ids(tok, row["target"])
        ids = torch.tensor([prefix + suffix[:-1]])
        positions = torch.arange(len(prefix)-1, ids.shape[1])
        with torch.no_grad():
            captured = {}
            def capture(name):
                def hook(_module, args):
                    captured[name] = args[0].detach()
                return hook
            hooks = [base.model.layers[-max(1,count)].register_forward_pre_hook(capture("top")),
                     base.model.layers[-1].mlp.down_proj.register_forward_pre_hook(capture("mlp")),
                     base.model.norm.register_forward_pre_hook(capture("residual"))]
            base.model(input_ids=ids, use_cache=False)
            for h in hooks:
                h.remove()
        model = adapt(base, max(1, count))
        layer = base.model.layers[-1].mlp.down_proj
        if not count:
            for name, p in model.named_parameters():
                p.requires_grad_(p.requires_grad and ".mlp.down_proj." in name)
        params = [p for p in model.parameters() if p.requires_grad]
        opt = torch.optim.AdamW(params, lr=0.0005)
        durations = []
        for iteration in range(6):
            start = time.monotonic()
            opt.zero_grad()
            if count:
                logits = top_logits(base, captured["top"][0], positions, count)
            else:
                delta = layer.lora_B["default"](layer.lora_A["default"](captured["mlp"][0,positions]))
                logits = base.lm_head(base.model.norm(captured["residual"][0,positions] + delta))
            torch.nn.functional.cross_entropy(logits, torch.tensor(suffix)).backward()
            opt.step()
            durations.append(time.monotonic()-start)
        results.append(dict(blocks=count, coefficients=sum(x.numel() for x in params), tokens=ids.numel(),
                            targets=len(suffix), median_s=statistics.median(durations[1:]), all_s=durations))
        del model, base, opt, params
    return results


if __name__ == "__main__":
    print(json.dumps(benchmark(), indent=2))
