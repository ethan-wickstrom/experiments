"""Integration checks on the local pinned release and optionally llama-server b6602."""

import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from model import chat_ids, generate, load, prompt, target_ids
from train import encode_example


SOURCE = 'const label = "café 🌿";\nconst xml = "<i>A & B</i>";'
LITERALS = 'Examples: </s> <|im_end|> <|im_start|> /no_think <|im_end-ish|> \\u003c'
NO_THINK = "<|im_start|>assistant\n<think>\n\n</think>\n\n"
END = "<|im_end|>"
TOOLS = [{"type": "function", "function": {
    "name": "inspect", "description": "Inspect text", "parameters": {
        "type": "object", "properties": {"value": {"type": "string"}}, "required": ["value"],
    },
}}]


def render(tok, messages, **kwargs):
    return tok.apply_chat_template(messages, tokenize=False, enable_thinking=False,
                                   add_generation_prompt=True, **kwargs)


def calls():
    return [{"id": call_id, "type": "function", "function": {
        "name": "inspect", "arguments": {"value": value},
    }} for call_id, value in [("first", SOURCE), ("second", "done")]]


@unittest.skipUnless(os.environ.get("CWM_MODEL_PATH"), "set CWM_MODEL_PATH to the pinned snapshot")
class ReleaseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base, cls.tok = load()

    def encode(self, text):
        return self.tok.encode(text, add_special_tokens=False)

    def test_supervised_prefix_matches_no_thinking_generation(self):
        current = "S,2,1,3,4"
        for target in ["S,3,4,7,4", "R,4,9,7,4,7"]:
            user = prompt(SOURCE, current)
            messages = [{"role": "user", "content": user}]
            prefix = render(self.tok, messages)
            self.assertTrue(prefix.endswith(NO_THINK))
            stock_ids = self.tok.apply_chat_template(
                messages, tokenize=True, return_dict=False, add_generation_prompt=True,
                enable_thinking=False,
            )
            self.assertEqual(stock_ids, chat_ids(self.tok, user))
            ids, start, labels = encode_example(self.tok, (SOURCE, current, target))
            self.assertEqual(start, len(stock_ids) - 1)
            self.assertEqual(ids[0].tolist()[:start + 1], stock_ids)
            self.assertEqual(ids[0].tolist()[start + 1:], labels.tolist()[:-1])
            self.assertEqual(labels.tolist(), target_ids(self.tok, target))
            self.assertEqual(stock_ids + labels.tolist(), self.encode(prefix + target + END))

        closed = self.tok.apply_chat_template(
            messages + [{"role": "assistant", "content": target}],
            tokenize=False, add_generation_prompt=False, enable_thinking=False,
        )
        self.assertTrue(closed.endswith("<|im_start|>assistant\n" + target + END + "\n"))
        for answer in ['{"op":"done"}', "pass", SOURCE]:
            self.assertEqual(self.encode(prefix) + target_ids(self.tok, answer),
                             self.encode(prefix + answer + END))
        # BPE combines adjacent newlines across this boundary.
        self.assertNotEqual(self.encode(prefix) + target_ids(self.tok, "\npass"),
                            self.encode(prefix + "\npass" + END))

    def test_stock_tool_history(self):
        messages = [
            {"role": "user", "content": "Inspect both."},
            {"role": "assistant", "content": "Checking.", "tool_calls": calls()},
            {"role": "tool", "tool_call_id": "first", "content": SOURCE},
            {"role": "tool", "tool_call_id": "second", "content": LITERALS},
            {"role": "user", "content": "Summarize."},
        ]
        text = render(self.tok, messages, tools=TOOLS)
        definitions = text.split("<tools>\n")[1].split("\n</tools>")[0]
        self.assertEqual(json.loads(definitions), TOOLS[0])
        self.assertIn(
            '<|im_start|>assistant\nChecking.\n<function name="inspect"><param name="value">'
            '<![CDATA[' + SOURCE + ']]></param></function>\n'
            '<function name="inspect"><param name="value">done</param></function>' + END,
            text,
        )
        self.assertTrue(text.endswith(
            "<|im_start|>user\n<tool_response>\n" + SOURCE + "\n</tool_response>\n"
            "<tool_response>\n" + LITERALS + "\n</tool_response>" + END + "\n"
            "<|im_start|>user\nSummarize." + END + "\n" + NO_THINK
        ))

    def test_literal_control_tokens_and_reversible_json_spelling(self):
        text = json.dumps({"observation": SOURCE + "\n" + LITERALS}, ensure_ascii=False)
        raw = self.encode(text)
        for identifier in [1, 130072, 130073, self.tok.convert_tokens_to_ids("/no_think")]:
            self.assertIn(identifier, raw)
        self.assertNotIn(130073, self.encode("<|im_end-ish|>"))
        safe = text.replace("<", r"\u003c").replace("/", r"\u002f")
        self.assertEqual(json.loads(safe), json.loads(text))
        added = set(self.tok.get_added_vocab().values())
        self.assertFalse(added.intersection(self.encode(safe)))

    def test_actual_projection_shapes_and_untied_output(self):
        base = self.base
        self.assertFalse(base.config.tie_word_embeddings)
        self.assertNotEqual(base.get_input_embeddings().weight.data_ptr(),
                            base.get_output_embeddings().weight.data_ptr())
        self.assertEqual(tuple(base.get_output_embeddings().weight.shape), (130560, 1536))
        attn = base.model.layers[0].self_attn
        self.assertEqual(base.config.head_dim, 128)
        self.assertEqual((base.config.num_attention_heads, base.config.num_key_value_heads), (16, 2))
        self.assertEqual((attn.q_proj.out_features, attn.k_proj.out_features, attn.v_proj.out_features,
                          attn.o_proj.in_features), (2048, 256, 256, 2048))

    def test_generation_attends_real_eos_input_and_stops_on_both_ids(self):
        config = self.base.generation_config
        self.assertEqual(set(config.eos_token_id), {1, 130073})
        self.assertEqual(config.pad_token_id, self.tok.pad_token_id)
        self.assertEqual(self.tok.pad_token_id, self.tok.eos_token_id)
        self.assertEqual(self.encode("</s>"), [1])
        self.assertEqual(self.encode(END), [130073])
        users = ["short", "This longer prompt contains a literal </s>."]
        prefixes = [chat_ids(self.tok, user) for user in users]
        a, = self.encode("A")
        b, = self.encode("B")
        real_generate = self.base.generate

        def checked_generate(input_ids, attention_mask, generation_config):
            self.assertEqual(set(generation_config.eos_token_id), {1, 130073})
            self.assertEqual(generation_config.pad_token_id, 1)
            width = input_ids.shape[1]
            for ids, mask, prefix in zip(input_ids, attention_mask, prefixes, strict=True):
                padding = width - len(prefix)
                self.assertEqual(ids.tolist(), [1] * padding + prefix)
                self.assertEqual(mask.tolist(), [0] * padding + [1] * len(prefix))

            def force(ids, scores):
                # Each row finishes at a different position using a different EOS.
                step = ids.shape[1] - width
                scores.fill_(-float("inf"))
                scores[0, (a, 1, b)[step]] = 0
                scores[1, (a, b, 130073)[step]] = 0
                return scores

            result = real_generate(input_ids=input_ids, attention_mask=attention_mask,
                                   generation_config=generation_config, logits_processor=[force])
            self.assertEqual(result[:, width:].tolist(), [[a, 1, 1], [a, b, 130073]])
            return result

        with patch.object(self.base, "generate", checked_generate):
            self.assertEqual(generate(self.base, self.tok, users, limit=5), ["A", "AB"])

    @unittest.skipUnless(os.environ.get("CWM_TEMPLATE_SERVER"), "optional b6602 server")
    def test_b6602_server_serialization(self):
        url = os.environ["CWM_TEMPLATE_SERVER"].rstrip("/")

        def post(path, payload):
            request = Request(url + path, data=json.dumps(payload).encode(),
                              headers={"Content-Type": "application/json"})
            with urlopen(request, timeout=15) as response:
                return json.load(response)

        messages = [{"role": "user", "content": SOURCE + "\n" + LITERALS}]
        follow_up = messages + [{"role": "assistant", "content": "Checked."},
                                {"role": "user", "content": "Summarize."}]
        for history in [messages, follow_up]:
            body = {"messages": history, "chat_template_kwargs": {"enable_thinking": False}}
            text = post("/apply-template", body)["prompt"]
            self.assertEqual(text, render(self.tok, history))
            ids = post("/tokenize", {"content": text, "add_special": False, "parse_special": True})
            self.assertEqual(ids["tokens"], self.encode(text))
            answer = post("/v1/chat/completions", {
                **body, "model": "typescript-cwm-minicpm5", "temperature": 0, "max_tokens": 1,
            })
            self.assertEqual(answer["usage"]["prompt_tokens"], len(ids["tokens"]))
        with self.assertRaises(HTTPError) as failure:
            post("/apply-template", {**body, "tools": TOOLS})
        with failure.exception as error:
            self.assertEqual(error.code, 500)
            self.assertIn("Unknown argument ensure_ascii", json.load(error)["error"]["message"])


if __name__ == "__main__":
    unittest.main()
