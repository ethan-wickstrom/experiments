"""No credential value leaves frond in an export or a headless log (ledger B12)."""

from __future__ import annotations

import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from frond import events as ev
from frond.agent.redact import Redactor
from frond.agent.scripted import Step
from frond.cli import export_run
from frond.printer import Printer
from tests.helpers import WorkspaceCase, scripted_agent

KEY = "sk-ant-api03-" + "Q" * 40
TOKEN = "ghp_" + "a1" * 18
ENV = {"ANTHROPIC_API_KEY": KEY, "MY_SERVICE_TOKEN": "hunter2-correct-horse", "AUTH_MODE": "on", "HOME": "/root"}


class RedactorTest(unittest.TestCase):
    def test_credential_values_key_shapes_and_url_passwords_go(self):
        redact = Redactor(ENV)
        text = f"key={KEY} token=hunter2-correct-horse gh={TOKEN} url=https://bob:pa55word@example.com/x mode=on"
        clean = redact(text)
        self.assertNotIn(KEY, clean)
        self.assertNotIn("hunter2-correct-horse", clean)
        self.assertNotIn(TOKEN, clean)
        self.assertNotIn("pa55word", clean)
        self.assertIn("[redacted $ANTHROPIC_API_KEY]", clean)
        self.assertIn("[redacted $MY_SERVICE_TOKEN]", clean)
        self.assertIn("mode=on", clean)  # too short to be told from ordinary text
        self.assertIn("/root", redact("HOME is /root"))  # not a credential by name

    def test_ordinary_text_is_unchanged(self):
        text = "def skip_tokens(sk): return sk  # AKIA is a prefix, not a key"
        self.assertEqual(Redactor({})(text), text)


class ExportRedactionTest(WorkspaceCase):
    def test_a_key_printed_by_a_step_is_not_exported(self):
        steps = [
            Step("Show the config.", f"print('loaded key {KEY}')"),
            Step("Answer.", f"SUBMIT(response='the key is {KEY}')"),
        ]
        agent, _ = scripted_agent(self, steps)
        agent.run_turn("what is in the config?")
        out = Path(tempfile.mkdtemp(prefix="frond-export-"))
        self.addCleanup(shutil.rmtree, out, True)
        with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": KEY}):
            export_run(agent, out)
        for name in ("steps.jsonl", "answer.md", "usage.json", "calls.jsonl", "metrics.json"):
            self.assertNotIn(KEY, (out / name).read_text(), name)
        records = [json.loads(line) for line in (out / "steps.jsonl").read_text().splitlines()]
        self.assertIn("[redacted $ANTHROPIC_API_KEY]", records[1]["output"])
        self.assertIn("[redacted $ANTHROPIC_API_KEY]", (out / "answer.md").read_text())


class PrinterRedactionTest(unittest.TestCase):
    def test_the_headless_log_and_answer_are_redacted(self):
        out, err = io.StringIO(), io.StringIO()
        printer = Printer(out, err, color=False, redact=Redactor({"ANTHROPIC_API_KEY": KEY}))
        printer(ev.Notice("info", f"using {KEY}"))
        printer(ev.TurnFinished(turn=1, response=f"done with {KEY}", status="done", error=None, duration=1.0, steps=1))
        self.assertNotIn(KEY, out.getvalue() + err.getvalue())
        json_out = io.StringIO()
        Printer(json_out, io.StringIO(), json_mode=True, redact=Redactor({"ANTHROPIC_API_KEY": KEY}))(
            ev.Notice("info", KEY)
        )
        self.assertNotIn(KEY, json_out.getvalue())


if __name__ == "__main__":
    unittest.main()
