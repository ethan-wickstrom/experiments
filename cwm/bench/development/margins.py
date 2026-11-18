"""Single-position label margins for fixed alternatives. No fitting or oracle inputs."""
import json
import sys
from contextlib import nullcontext

import torch

from corpus import HERE, verify_arm
from model import adapted, chat_ids, load


@torch.inference_mode()
def compare(prompts):
    for arm in ("B", "C"):
        verify_arm(arm)
    base, tokenizer = load()
    model = adapted(base, HERE / "B/peft")
    model.load_adapter(HERE / "C/peft", adapter_name="joint")
    result = {}
    for arm in ("A", "B", "C"):
        model.set_adapter("joint" if arm == "C" else "default")
        with model.disable_adapter() if arm == "A" else nullcontext():
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
    print(json.dumps(compare(json.load(sys.stdin))))
