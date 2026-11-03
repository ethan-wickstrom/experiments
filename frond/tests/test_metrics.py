"""What a run did, counted and exported for research (ledger B2)."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from dspy.utils.exceptions import AdapterParseError

from frond.agent.adapter import FrondAdapter
from frond.agent.metrics import RunMetrics, normalize_usage
from frond.agent.prompts import CodingTurn
from frond.agent.rlm import FrondRLM
from frond.agent.scripted import Step
from frond.cli import export_run
from tests.helpers import WorkspaceCase, scripted_agent


class NormalizeUsageTest(unittest.TestCase):
    def test_anthropic_counts_cache_outside_input_tokens(self):
        raw = {
            "input_tokens": 200,
            "cache_read_input_tokens": 9000,
            "cache_creation_input_tokens": 800,
            "output_tokens": 300,
        }
        self.assertEqual(
            normalize_usage(raw),
            {"input": 10_000, "cache_read": 9000, "cache_write": 800, "output": 300, "reasoning": 0},
        )

    def test_openai_style_usage_already_includes_cached_tokens(self):
        raw = {
            "prompt_tokens": 10_000,
            "completion_tokens": 300,
            "prompt_tokens_details": {"cached_tokens": 9000},
            "completion_tokens_details": {"reasoning_tokens": 120},
        }
        self.assertEqual(
            normalize_usage(raw),
            {"input": 10_000, "cache_read": 9000, "cache_write": 0, "output": 300, "reasoning": 120},
        )


class ParseFailureTest(unittest.TestCase):
    def test_a_reply_that_does_not_parse_is_counted(self):
        metrics = RunMetrics()
        signature = FrondRLM(CodingTurn)._action_signature_for_current_factory(None, "")
        with self.assertRaises(AdapterParseError):
            FrondAdapter(metrics=metrics).parse(signature, "no field markers at all")
        self.assertEqual(metrics.parse_failures, 1)


class ExportTest(WorkspaceCase):
    files = {"notes.txt": "hello\n"}  # noqa: RUF012

    def test_the_export_counts_syntax_errors_tool_calls_and_failed_edits(self):
        steps = [
            Step("broken", "def broken(:"),
            Step("edit a missing file", "edit('missing.txt', 'a', 'b')"),
            Step("edit for real", "edit('notes.txt', 'hello', 'goodbye')"),
            Step("done", "SUBMIT(response='done')"),
        ]
        agent, _ = scripted_agent(self, steps)
        agent.run_turn("tidy the notes")
        out = Path(tempfile.mkdtemp(prefix="frond-export-"))
        self.addCleanup(shutil.rmtree, out, True)
        export_run(agent, out)
        metrics = json.loads((out / "metrics.json").read_text())
        self.assertEqual(metrics["syntax_errors"], 1)
        self.assertEqual(metrics["tool_calls"]["edit"], 2)
        self.assertEqual(metrics["tool_failures"], {"edit": 1})
        self.assertEqual(metrics["failed_edits"], 1)
        self.assertEqual((metrics["turns"], metrics["steps"]), (1, 4))
        calls = [json.loads(line) for line in (out / "calls.jsonl").read_text().splitlines()]
        self.assertTrue(calls)
        self.assertTrue(all({"role", "model", "usage", "raw_usage"} <= set(c) for c in calls))


if __name__ == "__main__":
    unittest.main()
