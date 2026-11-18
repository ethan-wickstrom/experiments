"""Convert with official llama.cpp and compare every exported FP32 coefficient."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file

from corpus import HERE
from provenance import verified_base

CONVERTER_REV = "a300a9c33462f23d9d61e951650d249486f2b0f6"


def export(checkout, source, output):
    head = subprocess.check_output(["git", "-C", checkout, "rev-parse", "HEAD"], text=True).strip()
    if head != CONVERTER_REV:
        raise ValueError("Wrong llama.cpp converter revision")
    sys.path.insert(0, str(checkout / "gguf-py"))
    import gguf
    with verified_base(os.environ["CWM_MODEL_PATH"]) as snapshot:
        subprocess.run([sys.executable,str(checkout / "convert_lora_to_gguf.py"),
                        "--base",str(snapshot),"--outtype","f32","--outfile",str(output),str(source)],check=True)
    reader = gguf.GGUFReader(str(output))
    trained = load_file(source / "adapter_model.safetensors")
    assert len(reader.tensors) == len(trained) == 2
    for tensor in reader.tensors:
        role = {"blk.23.ffn_down.weight.lora_a":"lora_A", "blk.23.ffn_down.weight.lora_b":"lora_B"}[tensor.name]
        key, = [k for k in trained if k.endswith(role + ".weight")]
        np.testing.assert_array_equal(tensor.data,trained[key],strict=True)
    alpha = reader.get_field("adapter.lora.alpha").contents()
    assert float(alpha) == 16
    print(f"Verified {output}: {sum(w.size for w in trained.values())} FP32 coefficients")


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("checkout",type=Path)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    export(args.checkout,args.source,args.output)
