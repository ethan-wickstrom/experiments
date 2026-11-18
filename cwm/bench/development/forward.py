"""Persistent HF tensor backend for the Bun evaluator. One line per batch or loss request."""
import json
import sys

from corpus import HERE
from model import adapted, generate, load
from provenance import file_hash
from score import token_loss

arm, = sys.argv[1:]
if arm not in ("A", "B", "C"):
    raise ValueError("Expected A, B or C")
base, tok = load(verify_local=True)
model = base
if arm != "A":
    pins = json.loads((HERE / "artifacts.json").read_text())[arm]
    path = HERE / arm / "peft"
    for name in ("adapter_config.json", "adapter_model.safetensors"):
        if file_hash(path / name) != pins["peft/" + name]:
            raise ValueError(f"Changed {arm} adapter: {name}")
    model = adapted(base,path)
for line in sys.stdin:
    request = json.loads(line)
    if set(request) == {"prompts"}:
        response = generate(model, tok, request["prompts"], limit=32)
    elif set(request) == {"loss_rows"}:
        response = token_loss(base,tok,request["loss_rows"])
    else:
        raise ValueError("Unknown tensor request")
    print(json.dumps(response,ensure_ascii=False),flush=True)
