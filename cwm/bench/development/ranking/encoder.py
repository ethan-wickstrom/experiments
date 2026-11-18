"""Frozen CPU encoders for the ranker. No oracle or corpus access at inference."""
import json
import re
import sys
from pathlib import Path

import torch
import torch.nn.functional as F
from safetensors.torch import load_file

HERE = Path(__file__).resolve().parent
C2 = HERE.parent / "c2"
sys.path.append(str(HERE.parents[1] / "minicpm"))
from model import load
from provenance import file_hash

ARMS = ("A", "B2", "C2")
WEIGHTS = {
    "B2": "16576944ce670148ea84b611678335d02c42d983d695930dc0933d64da5d3220",
    "C2": "b9fb5a3ad9c501210deefd63fcf9a67f727e0cf52a0933af34414566d7a84043",
}
JUDGE = "Does the proposed replacement satisfy the goal and visible tests? Reply with pass or fail."
CHOOSE = "Which replacement satisfies the goal and visible tests? Reply with A or B."


def wire(value):
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    text = re.sub(r"[\ud800-\udfff]", lambda m: "\\u%04x" % ord(m[0]), text)
    return re.sub(r"/(?=(?:no_)?think)", lambda _: "\\u002f", text.replace("<", "\\u003c"))


def request(value):
    if not isinstance(value, dict) or set(value) != {"goal", "path", "files", "candidates"}:
        raise ValueError("Expected goal, path, files, candidates")
    goal, path = value["goal"], value["path"]
    if not isinstance(goal, str) or not isinstance(path, str) or not path:
        raise ValueError("Expected a string goal and nonempty path")
    files = value["files"]
    if not isinstance(files, list) or not all(
        isinstance(f, dict) and set(f) == {"path", "text"} and
        isinstance(f["path"], str) and isinstance(f["text"], str) for f in files
    ):
        raise ValueError("Expected visible files with string path and text")
    names = [f["path"] for f in files]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate visible path")
    files = [{"path": f["path"], "text": f["text"]} for f in
             sorted(files, key=lambda f: f["path"].encode("utf-16-be", errors="surrogatepass"))]
    writes = value["candidates"]
    if not isinstance(writes, list) or len(writes) != 2 or not all(
        isinstance(w, dict) and set(w) == {"op", "path", "text"} and w["op"] == "write" and
        w["path"] == path and isinstance(w["text"], str) for w in writes
    ):
        raise ValueError("Expected exactly two complete writes to the selected file")
    return dict(goal=goal, path=path, files=files), [
        dict(op="write", path=path, text=w["text"]) for w in writes
    ]


def single(state, candidate, first):
    payload = {"candidate": candidate, **state} if first else {**state, "candidate": candidate}
    user = JUDGE + "\n" + wire(payload)
    spans = {"goal": [], "checks": []}
    if first:
        # Only score tokens fully inside the escaped string contents. Find
        # fields structurally in serialization order, even if strings repeat.
        start = len(JUDGE + "\n" + '{"candidate":' + wire(candidate) + ',"goal":"')
        spans["goal"].append((start, start + len(wire(state["goal"])) - 2))
        start = user.index(',"files":[', start + len(wire(state["goal"])) - 2) + len(',"files":[')
        for f in state["files"]:
            text_at = start + len('{"path":' + wire(f["path"]) + ',"text":"')
            if re.search(r"(^|/)(__tests__/|test/|tests/)|[.](test|spec)[.]", f["path"]):
                spans["checks"].append((text_at, text_at + len(wire(f["text"])) - 2))
            start += len(wire(f)) + 1
    return user, spans


def comparison(state, left, right):
    return CHOOSE + "\n" + wire({"A": left, "B": right, **state})


class Encoder:
    def __init__(self, arms, max_tokens=4096):
        self.base, self.tok = load()
        self.arms = tuple(arms)
        self.max_tokens = min(max_tokens, self.base.config.max_position_embeddings)
        self.factors = {}
        for arm in self.arms:
            if arm == "A":
                continue
            path = C2 / arm / "peft/adapter_model.safetensors"
            if file_hash(path) != WEIGHTS[arm]:
                raise ValueError(f"Changed {arm} adapter")
            matrices = load_file(path)
            self.factors[arm] = tuple(matrices[f"base_model.model.model.layers.23.mlp.down_proj.lora_{s}.weight"]
                                      for s in ("A", "B"))
        for word in ("pass", "fail", "A", "B"):
            token, = self.tok.encode(word, add_special_tokens=False)
            setattr(self, word + "_id", token)

    @torch.inference_mode()
    def hidden(self, arm, inputs, residuals):
        if arm in self.factors:
            a, b = self.factors[arm]
            residuals = residuals + F.linear(F.linear(inputs, a), b)
        return self.base.model.norm(residuals)

    def margin(self, h, positive, negative):
        # Only two output rows contribute to a logit difference.
        weight = self.base.lm_head.weight
        return torch.mv(weight[[positive, negative]], h).diff().neg()

    @torch.inference_mode()
    def read(self, user, spans, compare=False):
        rendered = self.tok.apply_chat_template(
            [{"role": "user", "content": user}], tokenize=False,
            add_generation_prompt=True, enable_thinking=False,
        )
        encoded = self.tok(rendered, add_special_tokens=False, return_offsets_mapping=True)
        ids = torch.tensor(encoded["input_ids"])
        if len(ids) > self.max_tokens:
            raise ValueError(f"Full input has {len(ids)} tokens, limit {self.max_tokens}")
        offset = rendered.index(user)
        tokens = {
            name: [i for i, (a, b) in enumerate(encoded["offset_mapping"])
                   if a < b and any(offset + lo <= a and b <= offset + hi for lo, hi in ranges)]
            for name, ranges in spans.items()
        }
        captured = {}

        def capture(key):
            def hook(_module, args):
                captured[key] = args[0][0]
            return hook

        down = self.base.model.layers[-1].mlp.down_proj
        hooks = [down.register_forward_pre_hook(capture("input")),
                 self.base.model.norm.register_forward_pre_hook(capture("residual"))]
        try:
            self.base.model(input_ids=ids.unsqueeze(0), use_cache=False)
        finally:
            for hook in hooks:
                hook.remove()
        result = {}
        for arm in self.arms:
            h = self.hidden(arm, captured["input"], captured["residual"])
            if compare:
                result[arm] = {"comparison": self.margin(h[-1], self.A_id, self.B_id)}
                continue
            features = {"final": h[-1].clone(), "margin": self.margin(h[-1], self.pass_id, self.fail_id)}
            for name, idx in tokens.items():
                positions = torch.tensor(idx, dtype=torch.long)
                if name == "goal":
                    features["goal_state"] = h[positions].mean(0) if idx else torch.zeros_like(h[-1])
                # Predict visible text at t from the representation at t-1.
                total = 0.0
                for chunk in positions.split(32):
                    if len(chunk):
                        total -= F.cross_entropy(self.base.lm_head(h[chunk - 1]), ids[chunk],
                                                 reduction="sum").item()
                features[name + "_logp"] = torch.tensor([total / max(len(idx), 1)])
            result[arm] = features
        return result

    def difference(self, value, ablations=False):
        state, writes = request(value)
        diffs = {arm: {} for arm in self.arms}
        for first in ([False, True] if ablations else [True]):
            sides = [self.read(*single(state, w, first)) for w in writes]
            for arm in self.arms:
                prefix = "first_" if first else "last_"
                for name in sides[0][arm]:
                    if first or name in ("final", "margin"):
                        diffs[arm][prefix + name] = sides[0][arm][name] - sides[1][arm][name]
        ordered = [self.read(comparison(state, writes[i], writes[1-i]), {}, compare=True) for i in (0, 1)]
        for arm in self.arms:
            diffs[arm]["comparison"] = (ordered[0][arm]["comparison"] - ordered[1][arm]["comparison"]) / 2
        return diffs
