"""Boundary, candidate-exchange, and live PEFT equivalence checks."""
import copy
import json
import subprocess
import unittest

import torch
from peft import PeftModel
from build import episodes
from encoder import ARMS, C2, Encoder, request, single, wire
from head import response
from model import chat_ids


class Ranking(unittest.TestCase):
    def test_c2_json_bytes_and_span_boundaries(self):
        # Repeated source, control-looking literals, UTF-16 path sorting,
        # quotes and newlines must survive without changing model control IDs.
        payload = "a🧪\n\"\\ </s> <|im_end|> /think /no_think \\u003c"
        state = {"goal": payload, "path": "a.ts", "files": [
            {"path": "🧪.test.ts", "text": payload}, {"path": "a.ts", "text": payload},
            {"path": "\uffff.ts", "text": payload}]}
        candidate = {"op": "write", "path": "a.ts", "text": payload}
        checked, _ = request({**state, "candidates": [candidate, candidate]})
        expected = subprocess.run(["bun", "-e",
            'import { edit } from "./wire.ts"; const s=JSON.parse(await Bun.stdin.text());'
            'process.stdout.write(edit(s.goal,s.path,s.files).split("\\n")[1])'],
            cwd=C2, input=json.dumps(state), text=True, capture_output=True, check=True).stdout
        self.assertEqual(wire(checked), expected)
        user, spans = single(checked, candidate, first=True)
        self.assertEqual(json.loads(user.split("\n", 1)[1]), {"candidate": candidate, **checked})
        for name in ("goal", "checks"):
            (start, end), = spans[name]
            self.assertEqual(user[start:end], wire(payload)[1:-1])

    def test_oracle_is_outside_request(self):
        records = episodes()
        for index, (family, turn, value, choice) in enumerate(records):
            self.assertEqual(1-choice, records[index^1][-1])
            self.assertEqual(value["candidates"], records[index^1][2]["candidates"])
            extra = dict(value, observed=choice)
            with self.assertRaises(ValueError):
                request(extra)
            wrong = copy.deepcopy(value)
            wrong["candidates"][0]["path"] += " other file"
            with self.assertRaises(ValueError):
                request(wrong)
        self.assertEqual(response(0)["choice"], None)

    @torch.inference_mode()
    def test_live_peft_readout(self):
        encoder = Encoder(ARMS)
        state, writes = request(episodes()[0][2])
        user, spans = single(state, writes[0], first=True)
        expected = encoder.read(user, spans)
        ids = torch.tensor([chat_ids(encoder.tok, user)])
        base = encoder.base
        actual = base.model(input_ids=ids, use_cache=False).last_hidden_state[0, -1]
        torch.testing.assert_close(actual, expected["A"]["final"])
        peft = PeftModel.from_pretrained(base, C2 / "B2/peft", adapter_name="B2")
        peft.load_adapter(C2 / "C2/peft", adapter_name="C2")
        for arm in ("B2", "C2"):
            peft.set_adapter(arm)
            result = peft(input_ids=ids, use_cache=False, output_hidden_states=True)
            torch.testing.assert_close(result.hidden_states[-1][0, -1], expected[arm]["final"],
                                       rtol=2e-4, atol=2e-4)
            logits = result.logits[0, -1]
            torch.testing.assert_close((logits[encoder.pass_id] - logits[encoder.fail_id]).reshape(1),
                                       expected[arm]["margin"], rtol=2e-4, atol=2e-4)


if __name__ == "__main__":
    unittest.main()
