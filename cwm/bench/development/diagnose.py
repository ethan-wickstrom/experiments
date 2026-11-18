"""Teacher-forced token loss on the fit corpus. This is an in-sample diagnostic."""
import argparse
import json
from pathlib import Path

import torch
from safetensors.torch import load_file
from torch.nn.functional import cross_entropy, linear

from corpus import HERE, TRAINING_SHA
from features import CACHE_VERSION
from model import REVISION, load
from provenance import file_hash


@torch.inference_mode()
def measure(path):
    cache = torch.load(path,weights_only=True)
    assert (cache["version"],cache["revision"],cache["corpus"]) == (CACHE_VERSION, REVISION, TRAINING_SHA)
    base, _ = load(verify_local=True)
    pins = json.loads((HERE / "artifacts.json").read_text())
    result = {}
    for arm in ("A","B","C"):
        a = b = None
        if arm != "A":
            path = HERE / arm / "peft/adapter_model.safetensors"
            assert file_hash(path) == pins[arm]["peft/adapter_model.safetensors"]
            params = load_file(path)
            key, = [k for k in params if k.endswith("lora_A.weight")]
            a,b = params[key],params[key.replace("lora_A","lora_B")]
        result[arm] = {}
        for task,positions in cache["positions"].items():
            total, correct = 0.0, 0
            for idx in positions.split(48):
                residual = cache["residuals"][idx]
                if a is not None:
                    residual = residual + linear(linear(cache["inputs"][idx],a),b)
                logits = base.lm_head(base.model.norm(residual))
                labels = cache["labels"][idx]
                total += cross_entropy(logits,labels,reduction="sum").item()
                correct += (logits.argmax(-1) == labels).sum().item()
            result[arm][task] = dict(tokens=len(positions), nll=total/len(positions), top1=correct)
    return result


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("cache",type=Path)
    print(json.dumps(measure(p.parse_args().cache),indent=2))
