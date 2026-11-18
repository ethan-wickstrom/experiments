"""Shared MiniCPM5 loading, prompt format and lossless scalar frame projection."""

import gzip
import json
import os
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

MODEL_ID = "openbmb/MiniCPM5-1B"
REVISION = "ac83f813ba7da263c51a9f3ec37c2072597e54af"
DIRECTORY = Path(__file__).resolve().parent
ADAPTER = DIRECTORY / "adapter"
TRAIN = DIRECTORY.parent / "recurrent/data/fixed.jsonl.gz"
INSTRUCTION = (
    "Predict the next V8 pause after resume. Reply with one CSV row only. "
    "S,line,column,x,y for a step or R,line,column,x,y,value for a return. "
    "Lines and columns start at 1."
)


def load():
    torch.set_num_threads(int(os.environ.get("CWM_THREADS", "8")))
    path = os.environ.get("CWM_MODEL_PATH", MODEL_ID)
    tok = AutoTokenizer.from_pretrained(path, revision=REVISION)
    model = AutoModelForCausalLM.from_pretrained(
        path, revision=REVISION, dtype=torch.float32, attn_implementation="eager"
    ).eval()
    return model, tok


def prompt(source, current):
    return f"{INSTRUCTION}\n{source}\nCurrent: {current}\nAction: resume"


def chat_ids(tok, user):
    rendered = tok.apply_chat_template(
        [{"role": "user", "content": user}], tokenize=False,
        add_generation_prompt=True, enable_thinking=False,
    )
    return tok.encode(rendered, add_special_tokens=False)


def target_ids(tok, target):
    return tok.encode(target, add_special_tokens=False) + [tok.convert_tokens_to_ids("<|im_end|>")]


def scalar(snapshot):
    if snapshot["exact"] is not True or type(snapshot["value"]) is not int:
        raise ValueError(f"Expected an exact integer, got {snapshot!r}")
    return snapshot["value"]


def frame_row(frame, entry, fn):
    site, = frame["stack"]
    if site["file"] != entry or site["fn"] != fn or set(frame["locals"]) != {"x", "y"}:
        raise ValueError("Expected a single entry-function frame with exactly x and y")
    kind = {"step": "S", "return": "R"}[frame["kind"]]
    fields = [kind, site["line"], site["column"], *(scalar(frame["locals"][k]) for k in ("x", "y"))]
    if kind == "R":
        fields.append(scalar(frame["value"]))
    elif "value" in frame:
        raise ValueError("Unexpected payload")
    return ",".join(map(str, fields))


def examples(path):
    rows = []
    opener = gzip.open if Path(path).suffix == ".gz" else open
    with opener(path, "rt", encoding="utf8") as stream:
        for line in stream:
            run = json.loads(line)
            entry, fn = run["entry"], run["fn"]
            frames = run["frames"]
            if frames[0]["stack"][0]["fn"] != "" or len(frames) < 2:
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
