"""Regression checks for prefixes, stops, balanced draws and released adapter reload."""
import os
import unittest

import torch
from transformers import AutoTokenizer

from data import ROOT, encode, corpus
from fit import draws
from inference import decode
from package_model import verify
from provenance import verified_base
from safetensors.torch import load_file


class Weights(unittest.TestCase):
    def test_all_target_bytes_and_stop(self):
        with verified_base(os.environ["CWM_MODEL_PATH"]) as base:
            tok=AutoTokenizer.from_pretrained(base,local_files_only=True)
            for row in corpus():
                _,suffix=encode(tok,row)
                self.assertEqual(decode(tok,suffix),dict(text=row["target"],stopped=True,tokens=len(suffix)-1))
            for final in [1,130073]:
                text="  export const a = 1;\n"
                payload=tok.encode(text,add_special_tokens=False)
                self.assertEqual(decode(tok,payload+[final,17])["text"],text)
                self.assertFalse(decode(tok,payload)["stopped"])
            for text in ["</s>","<|im_end|>","/no_think","<think>"]:
                with self.assertRaises(ValueError):
                    encode(tok,dict(prompt="Source",target="const s = "+repr(text)))

    def test_balanced_updates(self):
        budget=512*64
        self.assertEqual(sum(draws("B2",i)["source"] for i in range(1,513)),round(budget*9/11))
        for i in range(1,513):
            self.assertEqual(sum(draws("B2",i).values()),64)
            self.assertEqual(sum(draws("C2",i).values()),64)

    def test_reloaded_state_matches_released_weights(self):
        for arm in ["C2","B2"]:
            verify(arm)
            checkpoint=torch.load(ROOT/arm/"state.pt",weights_only=True)
            released=load_file(ROOT/arm/"peft/adapter_model.safetensors")
            self.assertEqual(checkpoint["step"],512)
            for role,module in [("A","a"),("B","b")]:
                key,=[k for k in released if k.endswith("lora_"+role+".weight")]
                self.assertTrue(torch.equal(released[key],checkpoint[module]["weight"]))


if __name__=="__main__":
    unittest.main()
