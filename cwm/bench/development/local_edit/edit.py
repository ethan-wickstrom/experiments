"""Learned line-span and raw-replacement inference on visible project state."""
import argparse
import json
import sys

import torch
from transformers import GenerationConfig
from backbone import HERE, chat_ids, load
from model import adapted
from provenance import file_hash
from wire import inspect_request, lines, splice, user


class SpanGrammar:
    """Legal token continuations for decimal start:end with 0 <= start <= end <= n."""
    def __init__(self, tok, n, width, stops):
        self.width = width
        self.stops = stops
        self.colon, = tok.encode(":", add_special_tokens=False)
        self.numbers = [tuple(ids) for ids in tok([str(i) for i in range(n+1)],
                                                   add_special_tokens=False)["input_ids"]]
        self.value = {tokens: i for i, tokens in enumerate(self.numbers)}

    def __call__(self, batch_id, input_ids):
        part = tuple(input_ids[self.width:].tolist())
        after = self.colon in part
        floor = 0
        if after:
            colon = part.index(self.colon)
            floor = self.value[part[:colon]]
            part = part[colon+1:]
        allowed = {ids[len(part)] for ids in self.numbers[floor:]
                   if len(ids) > len(part) and ids[:len(part)] == part}
        if part in self.value and self.value[part] >= floor:
            allowed.update(self.stops if after else [self.colon])
        if not allowed:
            raise ValueError("Invalid span decoding prefix")
        return sorted(allowed)


class Editor:
    def __init__(self, arm, replacement_budget=96, max_input=4096):
        base, self.tok = load()
        self.model = base
        if arm == "trained":
            release = HERE / "model"
            pins = json.loads((release / "provenance.json").read_text())
            for name, sha in pins["files"].items():
                if file_hash(release/name) != sha:
                    raise ValueError(f"Changed local-edit artifact {name}")
            self.model = adapted(base, release/"peft")
        self.budget = replacement_budget
        self.max_input = min(max_input, base.config.max_position_embeddings)
        self.stops = [self.tok.eos_token_id, self.tok.convert_tokens_to_ids("<|im_end|>")]

    @torch.inference_mode()
    def generate(self, prompt, limit, boundaries=None):
        ids = chat_ids(self.tok, prompt)
        if len(ids) > self.max_input or len(ids)+limit > self.model.config.max_position_embeddings:
            raise ValueError(f"Complete prompt has {len(ids)} tokens, exceeds context budget")
        kwargs = {}
        if boundaries is not None:
            kwargs["prefix_allowed_tokens_fn"] = SpanGrammar(self.tok, boundaries, len(ids), self.stops)
        config = GenerationConfig(use_cache=True, do_sample=False, max_new_tokens=limit,
                                  eos_token_id=self.stops, pad_token_id=self.tok.pad_token_id)
        sequence = self.model.generate(input_ids=torch.tensor([ids]), attention_mask=torch.ones(1,len(ids),dtype=torch.long),
                                       generation_config=config, **kwargs)[0,len(ids):].tolist()
        if not sequence or sequence[-1] not in self.stops:
            return None
        return self.tok.decode(sequence[:-1], skip_special_tokens=False)

    def __call__(self, req):
        source = inspect_request(req)[req["path"]]
        location = self.generate(user(req), 16, len(lines(source)))
        if location is None:
            return {"stopped": False, "error": "location token cap"}
        start, end = map(int, location.split(":"))
        replacement = self.generate(user(req, (start,end)), self.budget)
        if replacement is None:
            return {"stopped": False, "error": "replacement token cap", "start":start, "end":end}
        return dict(stopped=True, start=start, end=end, replacement=replacement,
                    text=splice(source, start, end, replacement))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--serve", action="store_true")
    p.add_argument("--arm", choices=("trained","base"), default="trained")
    p.add_argument("--max-input", type=int, default=4096)
    p.add_argument("--replacement-budget", type=int, default=96)
    args = p.parse_args()
    if min(args.max_input,args.replacement_budget) < 1:
        p.error("Budgets must be positive")
    editor = Editor(args.arm, args.replacement_budget, args.max_input)
    if args.serve:
        for line in sys.stdin:
            try:
                result = editor(json.loads(line))
            except (ValueError,TypeError) as exc:
                result = {"stopped":False, "error":str(exc)}
            print(json.dumps(result, allow_nan=False), flush=True)
    else:
        print(json.dumps(editor(json.load(sys.stdin)), allow_nan=False))
