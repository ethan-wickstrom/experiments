"""Verify official data and encode targets behind exactly the inference prefix."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT.parent))
from corpus import canonical, verified
from model import TRAIN, chat_ids, examples, prompt, target_ids
from provenance import TRAIN_SHA

PROJECT_SHA = "d9bc52e6557f8f8a194566088dcabf1596ee49594d93c0be5aa8342c7afa5881"
ORACLE_SHA = "579596a65d87a88f1643dc39a617972d117bdbe01f2d144fdba899a2afcf6588"


def corpus():
    verified(ROOT / "data/oracle.jsonl.gz", ORACLE_SHA)
    projects = verified(ROOT / "data/projects.jsonl.gz", PROJECT_SHA)
    rows = [json.loads(line) for line in projects.splitlines()]
    for source, start, end in examples(TRAIN, expected_sha=TRAIN_SHA):
        family = "pause-" + hashlib.sha256(source.encode()).hexdigest()[:12]
        rows.append(dict(family=family, task="execution", prompt=prompt(source, start), target=end))
    return rows


def digest(rows):
    return hashlib.sha256(canonical(rows)).hexdigest()


def encode(tok, row):
    user, target = row["prompt"], row["target"]
    prefix = chat_ids(tok, user)
    suffix = target_ids(tok, target)
    # The raw assistant suffix is encoded independently, like server generation.
    # A completed training conversation rendered as a whole can use different
    # template text/BPE merges at its assistant boundary.
    reserved = set(tok.get_added_vocab().values())
    payload = tok.encode(user, add_special_tokens=False)
    if reserved.intersection(payload) or reserved.intersection(suffix[:-1]):
        raise ValueError("Control token inside raw payload")
    if tok.decode(suffix[:-1], skip_special_tokens=False) != target:
        raise ValueError("Target bytes do not round-trip")
    if suffix[-1] != 130073 or prefix != tok.apply_chat_template(
        [{"role":"user", "content":user}], tokenize=True,
        enable_thinking=False, add_generation_prompt=True)["input_ids"]:
        raise ValueError("Template prefix or stop mismatch")
    return prefix, suffix
