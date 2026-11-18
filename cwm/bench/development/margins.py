"""Single-position label margins for fixed alternatives. No fitting or oracle inputs."""
import json
import sys
from contextlib import nullcontext

import torch

from corpus import HERE, verify_arm
from model import adapted, chat_ids, load


@torch.inference_mode()
def compare(prompts, arms):
    for arm in arms:
        if arm in ("B", "C"):
            verify_arm(arm)
        elif arm in ("B2", "C2"):
            sys.path.insert(0, str(HERE / "c2"))
            from package_model import verify
            verify(arm)
        elif arm != "A":
            raise ValueError("Unknown arm: " + arm)
    base, tokenizer = load()
    model = base
    adapters = {}
    for arm in arms:
        if arm == "A":
            continue
        path = (HERE / "c2" if arm.endswith("2") else HERE) / arm / "peft"
        if not adapters:
            model = adapted(base, path)
            adapters[arm] = "default"
        else:
            model.load_adapter(path, adapter_name=arm)
            adapters[arm] = arm
    result = {}
    for arm in arms:
        if arm != "A":
            model.set_adapter(adapters[arm])
        with model.disable_adapter() if arm == "A" and adapters else nullcontext():
            answers = []
            for i, prompt in enumerate(prompts):
                yes, no = ("yes", "no") if i % 2 else ("pass", "fail")
                positive, = tokenizer.encode(yes, add_special_tokens=False)
                negative, = tokenizer.encode(no, add_special_tokens=False)
                prefix = chat_ids(tokenizer, prompt)
                logits = model(input_ids=torch.tensor([prefix]), use_cache=False,
                               logits_to_keep=1).logits[0, -1]
                answers.append(dict(margin=(logits[positive] - logits[negative]).item(),
                                    inputTokens=len(prefix)))
            result[arm] = answers
    return result


if __name__ == "__main__":
    print(json.dumps(compare(json.load(sys.stdin), sys.argv[1:] or ["A", "B", "C"])))
