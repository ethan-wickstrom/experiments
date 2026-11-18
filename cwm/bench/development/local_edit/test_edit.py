"""Boundary, tensor supervision and draw-schedule regression tests."""
import hashlib
import json
import os
import unittest
from collections import Counter

import torch
from transformers import AutoTokenizer
from edit import SpanGrammar
from local_data import HERE, authored, training, digest
from provenance import file_hash
from train_local import CORPUS, schedule
from wire import derive, inspect_request, lines, splice, user


class LocalEdit(unittest.TestCase):
    def test_untouched_bytes_and_minimal_splice(self):
        for before, after in [("", "x\n"), ("a\r\nb\r\n", "a\r\nc\r\n"),
                              ("head\nold\nend", "head\nend"), ("//🖌\nx\n", "//🖌\na\nb\nx\n"),
                              ("no final newline", "no final newline\n"), ("a\n", "a\n")]:
            start, end, repl = derive(before, after)
            self.assertEqual(splice(before, start, end, repl).encode(), after.encode())
            self.assertEqual("".join(lines(before)),before)
        for start, end in [(-1,0), (1,0), (0,2), (True,1)]:
            with self.assertRaises(ValueError):
                splice("x\n", start, end, "")

    def test_wire_visibility(self):
        source = "const t = '<|im_end|> /no_think';\r\n"
        req = dict(goal="Set the title.", path="m.ts", files=[dict(path="m.ts",text=source)])
        for prompt in [user(req), user(req,(0,1))]:
            self.assertNotIn("<|im_end|>", prompt)
            self.assertNotIn("/no_think", prompt)
            self.assertEqual(json.loads(prompt.split("\n",1)[1])["lines"], [[0,source]])
        with self.assertRaises(ValueError):
            inspect_request(dict(**req, future="pass"))

    def test_schedule_and_tape(self):
        rows = training()
        self.assertEqual(digest(rows), CORPUS)
        plan = schedule(rows)
        self.assertEqual(plan, schedule(rows))
        self.assertEqual(Counter(rows[i]["task"] for i in plan), dict(locate=768,fill=1024,execution=128,forecast=128))

    def test_grammar(self):
        tok = AutoTokenizer.from_pretrained(os.environ["CWM_MODEL_PATH"], local_files_only=True)
        stops=[tok.eos_token_id,tok.convert_tokens_to_ids("<|im_end|>")]
        for n in [0,12,104]:
            grammar=SpanGrammar(tok,n,0,stops)
            for start,end in ((0,0),(0,n),(n,n)):
                ids=tok.encode(f"{start}:{end}",add_special_tokens=False)
                for pos,id_ in enumerate(ids):
                    self.assertIn(id_,grammar(0,torch.tensor(ids[:pos])))
                self.assertTrue(set(stops) <= set(grammar(0,torch.tensor(ids))))
            if n:
                prefix=tok.encode(f"{n}:",add_special_tokens=False)
                self.assertNotIn(tok.encode("0",add_special_tokens=False)[0],grammar(0,torch.tensor(prefix)))

    def test_released_control(self):
        rows = training()
        held = {ep["family"] for ep, _ in authored("holdout")}
        self.assertEqual(len(held), 4)
        self.assertTrue(held.isdisjoint(r["family"] for r in rows))
        draws = [(step, i) for step, i in enumerate(schedule(rows), 1)
                 if rows[i]["task"] in ("locate", "fill")]
        fingerprint = hashlib.sha256(json.dumps(draws, separators=(",", ":")).encode()).hexdigest()
        fits = []
        for folder, arm, updates in [("model", "trained", 2048), ("edit-only", "edit-only", 1792)]:
            root = HERE / folder
            pins = json.loads((root / "provenance.json").read_text())
            fit = json.loads((root / "fit.json").read_text())
            self.assertEqual((pins["arm"], fit["arm"]), (arm, arm))
            for name, sha in pins["files"].items():
                self.assertEqual(file_hash(root / name), sha)
            self.assertEqual(fit["edit_plan_sha256"], fingerprint)
            self.assertEqual(fit["optimizer_steps"], updates)
            fits.append(fit)
        for key in ("revision", "corpus", "cache_sha256", "seed", "steps", "blocks", "initial_sha256"):
            self.assertEqual(fits[0][key], fits[1][key], key)
        self.assertNotEqual(fits[0]["peft_sha256"], fits[1]["peft_sha256"])


if __name__ == "__main__":
    unittest.main()
