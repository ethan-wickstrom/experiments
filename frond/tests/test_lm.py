"""What frond actually sends to Claude: effort set, no sampling parameters, and the native route kept (ledger B1)."""

from __future__ import annotations

import os
import unittest
import warnings
from typing import Any
from unittest import mock

from dspy._vendor.lm15.providers.anthropic import AnthropicLM

from frond.agent.lm import build_lm, clear_public_endpoint_overrides, native_route, route_of


class _Sent(Exception):
    pass


def sent_payload(lm) -> dict[str, Any]:
    """The JSON body frond's LM would POST to Anthropic, captured before anything leaves the process."""
    captured: dict[str, Any] = {}
    real = AnthropicLM._payload

    def spy(self, request, stream):
        captured.update(real(self, request, stream))
        raise _Sent

    with mock.patch.object(AnthropicLM, "_payload", spy), warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        try:
            lm(messages=[{"role": "user", "content": "Say hi"}])
        except Exception:  # _Sent, wrapped by DSPy's error boundary
            pass
    return captured


class LMTest(unittest.TestCase):
    def setUp(self) -> None:
        # as in a hosted session: a key, and the base URL set to Anthropic's own public endpoint
        env = {"ANTHROPIC_API_KEY": "sk-ant-test", "ANTHROPIC_BASE_URL": "https://api.anthropic.com"}
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_claude_gets_effort_and_no_sampling_parameters(self):
        lm = build_lm("anthropic/claude-opus-5-5", effort="high")
        self.assertEqual(route_of(lm), "native")
        payload = sent_payload(lm)
        self.assertEqual(payload["model"], "claude-opus-5-5")
        self.assertEqual(payload["output_config"], {"effort": "high"})
        self.assertEqual(payload["thinking"], {"type": "adaptive"})
        for name in ("temperature", "top_p", "top_k"):
            self.assertNotIn(name, payload)  # Claude 5.5 models answer these with HTTP 400

    def test_without_effort_the_model_default_applies(self):
        payload = sent_payload(build_lm("anthropic/claude-opus-5-5"))
        self.assertEqual(payload["model"], "claude-opus-5-5")
        self.assertNotIn("output_config", payload)

    def test_a_real_gateway_keeps_working_without_prompt_caching(self):
        os.environ["ANTHROPIC_BASE_URL"] = "https://llm-gateway.example.com"
        lm = build_lm("anthropic/claude-opus-5-5", effort="high")
        self.assertFalse(native_route(lm))
        self.assertIn("prompt caching is off", route_of(lm))
        self.assertIsNone(lm.kwargs.get("prompt_cache"))
        self.assertEqual(os.environ["ANTHROPIC_BASE_URL"], "https://llm-gateway.example.com")  # left alone

    def test_only_the_public_endpoint_is_cleared(self):
        self.assertEqual(clear_public_endpoint_overrides("anthropic/claude-opus-5-5"), ["ANTHROPIC_BASE_URL"])
        self.assertNotIn("ANTHROPIC_BASE_URL", os.environ)
        os.environ["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:8080"
        self.assertEqual(clear_public_endpoint_overrides("anthropic/claude-opus-5-5"), [])

    def test_unknown_effort_is_refused(self):
        with self.assertRaises(ValueError):
            build_lm("anthropic/claude-opus-5-5", effort="extreme")


if __name__ == "__main__":
    unittest.main()
