"""Shared MiniCPM5 loading, prompt format and lossless scalar frame projection."""

import gzip
import hashlib
import json
import os
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

from provenance import verify_base

MODEL_ID = "openbmb/MiniCPM5-1B"
REVISION = "ac83f813ba7da263c51a9f3ec37c2072597e54af"
DIRECTORY = Path(__file__).resolve().parent
ADAPTER = DIRECTORY / "adapter"
TRAIN = DIRECTORY.parent / "recurrent/data/fixed.jsonl.gz"
TEMPLATE = (DIRECTORY / "resume.txt").read_text(encoding="utf8").rstrip("\n")


def load(*, verify_local=False):
    torch.set_num_threads(int(os.environ.get("CWM_THREADS", "8")))
    path = os.environ.get("CWM_MODEL_PATH", MODEL_ID)
    if verify_local and path != MODEL_ID:
        verify_base(path)
    tok = AutoTokenizer.from_pretrained(path, revision=REVISION)
    model = AutoModelForCausalLM.from_pretrained(
        path, revision=REVISION, dtype=torch.float32, attn_implementation="eager"
    ).eval()
    return model, tok


def prompt(source, current):
    return TEMPLATE.format(source=source, current=current)


def chat_ids(tok, user):
    rendered = tok.apply_chat_template(
        [{"role": "user", "content": user}], tokenize=False,
        add_generation_prompt=True, enable_thinking=False,
    )
    return tok.encode(rendered, add_special_tokens=False)


def target_ids(tok, target):
    return tok.encode(target, add_special_tokens=False) + [tok.convert_tokens_to_ids("<|im_end|>")]


def safe_integer(value):
    return type(value) is int and abs(value) <= (1 << 53) - 1


def scalar(snapshot):
    if snapshot["exact"] is not True or not safe_integer(snapshot["value"]):
        raise ValueError(f"Expected an exact safe integer, got {snapshot!r}")
    return snapshot["value"]


def valid_fields(kind, values):
    return (
        len(values) == {"S": 4, "R": 5}.get(kind)
        and all(safe_integer(v) for v in values)
        and min(values[:2]) >= 1
    )


def valid_row(text):
    kind, *strings = text.split(",")
    if any(len(v) > 17 for v in strings):
        return False
    try:
        values = [int(v) for v in strings]
    except ValueError:
        return False
    return valid_fields(kind, values) and list(map(str, values)) == strings


def frame_row(frame, entry, fn):
    site, = frame["stack"]
    if site["file"] != entry or site["fn"] != fn or set(frame["locals"]) != {"x", "y"}:
        raise ValueError("Expected a single entry-function frame with exactly x and y")
    kind = {"step": "S", "return": "R"}[frame["kind"]]
    fields = [site["line"], site["column"], *(scalar(frame["locals"][k]) for k in ("x", "y"))]
    if kind == "R":
        fields.append(scalar(frame["value"]))
    elif "value" in frame:
        raise ValueError("Unexpected payload")
    if not valid_fields(kind, fields):
        raise ValueError("Expected positive coordinates and exact safe integer fields")
    return ",".join([kind, *map(str, fields)])


def parse_integer(token):
    if token == "-0":
        raise ValueError("Negative zero is outside the exact integer domain")
    return int(token)


def examples(path, *, expected_sha=None):
    rows = []
    opener = gzip.open if Path(path).suffix == ".gz" else open
    with opener(path, "rb") as stream:
        data = stream.read()
    if expected_sha is not None and hashlib.sha256(data).hexdigest() != expected_sha:
        raise ValueError(f"Normalized oracle tape digest mismatch: {path}")
    for line in data.splitlines():
        run = json.loads(line, parse_int=parse_integer)
        entry, fn = run["entry"], run["fn"]
        frames = run["frames"]
        if len(frames) < 2 or frames[0]["stack"][0]["fn"] != "":
            raise ValueError("Expected a module pause followed by function pauses")
        observed = [frame_row(f, entry, fn) for f in frames[1:]]
        for current, target in zip(observed, observed[1:]):
            rows.append((run["files"][entry], current, target))
    return rows


@torch.no_grad()
def generate(model, tok, users, limit):
    enc = [chat_ids(tok, user) for user in users]
    width = max(map(len, enc))
    ids = torch.tensor([[tok.pad_token_id] * (width - len(row)) + row for row in enc])
    mask = torch.tensor([[0] * (width - len(row)) + [1] * len(row) for row in enc])
    config = GenerationConfig(
        do_sample=False, max_new_tokens=limit, use_cache=True, pad_token_id=tok.pad_token_id,
        eos_token_id=[tok.eos_token_id, tok.convert_tokens_to_ids("<|im_end|>")],
    )
    result = model.generate(input_ids=ids, attention_mask=mask, generation_config=config)
    # Only remove padding and the actual stop. Preserve other special tokens as model output.
    stops = set(config.eos_token_id)
    texts = []
    for row in result[:, width:].tolist():
        end = next((i for i, token in enumerate(row) if token in stops), len(row))
        texts.append(tok.decode(row[:end], skip_special_tokens=False).strip())
    return texts


def adapted(model, path):
    return PeftModel.from_pretrained(model, str(path)).eval()
