"""Check the shipped snapshot identities and the exact training/inference token contract."""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import torch
from transformers import AutoTokenizer

from corpus import HERE, verify_arm
from model import chat_ids, generate, target_ids


class Artifacts(unittest.TestCase):
    def test_all_official_artifacts(self):
        for arm in ("B","C"):
            verify_arm(arm)

    def test_corrupt_optimizer_or_weights_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copy(HERE / "artifacts.json",root)
            shutil.copytree(HERE / "C",root / "C")
            for name in ("state.pt", "peft/adapter_model.safetensors"):
                path = root / "C" / name
                with path.open("ab") as f:
                    f.write(b"!")
                with self.assertRaisesRegex(ValueError,"Changed C artifact"):
                    verify_arm("C",root)
                shutil.copyfile(HERE / "C" / name,path)

    @unittest.skipUnless(os.environ.get("CWM_MODEL_PATH"), "requires local pinned tokenizer")
    def test_stock_chat_ids_masks_and_stops(self):
        tok = AutoTokenizer.from_pretrained(os.environ["CWM_MODEL_PATH"],local_files_only=True)
        state = dict(files=["a.ts"],history=[{"user":"Read a.ts."},
            {"action":{"op":"read","path":"a.ts"},"observed":'const s = "</s>";\n// x < y & café\n'},
            {"user":"Preserve the literal. Run the tests."}])
        user = "Choose one action.\n" + json.dumps(state,ensure_ascii=False,separators=(",",":"))
        msgs = [{"role":"user","content":user}]
        official = tok.apply_chat_template(msgs,tokenize=True,add_generation_prompt=True,enable_thinking=False)
        self.assertEqual(chat_ids(tok,user),official["input_ids"])
        self.assertEqual(target_ids(tok,"pass")[-1],130073)
        def fake(input_ids,attention_mask,generation_config):
            self.assertEqual(set(generation_config.eos_token_id),{1,130073})
            self.assertTrue(((input_ids[0] == 1) & (attention_mask[0] == 1)).any())
            self.assertTrue(((input_ids[1] == 1) & (attention_mask[1] == 0)).any())
            token, = tok.encode("pass",add_special_tokens=False)
            return torch.cat([input_ids,torch.tensor([[token,1,token],[token,130073,token]])],dim=1)
        m = Mock()
        m.generate.side_effect = fake
        self.assertEqual(generate(m,tok,[user,"Short"],3),["pass","pass"])


if __name__ == "__main__":
    unittest.main()
