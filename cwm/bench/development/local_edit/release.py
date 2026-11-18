"""Pin and validate both top-block LoRA factors per trained projection."""
import argparse
import json
from pathlib import Path

from safetensors.torch import load_file
from backbone import REVISION
from local_data import TRAIN
from provenance import BASE_FILES, file_hash
from train_local import CORPUS

FILES = ("fit.json", "peft/adapter_config.json", "peft/adapter_model.safetensors")


def package(root):
    fit = json.loads((root/"fit.json").read_text())
    config = json.loads((root/FILES[1]).read_text())
    tensors = load_file(root/FILES[2])
    assert config["r"] == config["lora_alpha"] == 32
    assert config["revision"] == REVISION == fit["revision"] and fit["corpus"] == CORPUS
    assert len(tensors) == 20 and sum(p.numel() for p in tensors.values()) == fit["coefficients"]
    for layer in (22,23):
        for mod in ("self_attn.q_proj","self_attn.k_proj","self_attn.v_proj","self_attn.o_proj","mlp.down_proj"):
            key = f"base_model.model.model.layers.{layer}.{mod}"
            a,b = [tensors[key + ".lora_" + name + ".weight"] for name in ("A","B")]
            assert a.shape[0] == b.shape[1] == 32 and a.isfinite().all() and b.isfinite().all() and b.any()
    pins = dict(arm=fit["arm"], revision=REVISION, base_files=BASE_FILES, train_sha256=TRAIN,
                corpus_sha256=CORPUS, files={name:file_hash(root/name) for name in FILES})
    assert pins["files"][FILES[2]] == fit["peft_sha256"]
    (root/"provenance.json").write_text(json.dumps(pins,indent=2)+"\n")
    print(pins["files"][FILES[2]])


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("model_dir",type=Path)
    package(p.parse_args().model_dir)
