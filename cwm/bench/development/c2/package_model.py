"""Export and pin the two trained tensors and the independently downloadable base GGUF."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file

from data import ROOT, corpus, digest
from export import CONVERTER_REV
from model import REVISION
from provenance import file_hash, verified_base

BASE_URL = "https://huggingface.co/openbmb/MiniCPM5-1B-GGUF/resolve/5385560dd3e232bcc3577fd9442c332cad2facbd/MiniCPM5-1B-F16.gguf"
BASE_HASH = "68c40b08b1242754a107b9510af89aa75b10c75843ca7844643c70956b7f1e3d"
NAMES = ["peft/adapter_model.safetensors","peft/adapter_config.json","adapter-f32.gguf","state.pt","fit.json"]


def verify(arm):
    pins=json.loads((ROOT / arm / "artifacts.json").read_text())
    assert pins["revision"] == REVISION and pins["corpus"] == digest(corpus())
    assert set(pins["files"]) == set(NAMES)
    for name in NAMES:
        if file_hash(ROOT / arm / name) != pins["files"][name]:
            raise ValueError("Changed " + arm + " artifact " + name)
    return pins


def ship(checkout, arm, base_gguf):
    output=ROOT / arm
    assert file_hash(base_gguf) == BASE_HASH
    assert subprocess.check_output(["git","-C",checkout,"rev-parse","HEAD"],text=True).strip()==CONVERTER_REV
    sys.path.insert(0,str(checkout / "gguf-py"))
    import gguf
    with verified_base(os.environ["CWM_MODEL_PATH"]) as base:
        subprocess.run([sys.executable,str(checkout/"convert_lora_to_gguf.py"),
                        "--base",str(base),"--outtype","f32","--outfile",str(output/"adapter-f32.gguf"),
                        str(output/"peft")],check=True)
    peft=load_file(output/"peft/adapter_model.safetensors")
    reader=gguf.GGUFReader(str(output/"adapter-f32.gguf"))
    assert float(reader.get_field("adapter.lora.alpha").contents()) == 32
    assert len(peft) == len(reader.tensors) == 2
    for t in reader.tensors:
        role={"blk.23.ffn_down.weight.lora_a":"lora_A","blk.23.ffn_down.weight.lora_b":"lora_B"}[t.name]
        key, = [k for k in peft if k.endswith(role+".weight")]
        np.testing.assert_array_equal(t.data, peft[key], strict=True)
    assert sum(v.size for v in peft.values()) == 196608
    pins=dict(revision=REVISION,corpus=digest(corpus()),base_gguf_url=BASE_URL,base_gguf_sha256=BASE_HASH,
              converter=CONVERTER_REV,files={n:file_hash(output/n) for n in NAMES})
    (output/"artifacts.json").write_text(json.dumps(pins,indent=2)+"\n")
    verify(arm)


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("checkout",type=Path)
    p.add_argument("arm",choices=["C2","B2"])
    p.add_argument("base_gguf",type=Path)
    args=p.parse_args()
    ship(args.checkout,args.arm,args.base_gguf)
