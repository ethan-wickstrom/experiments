"""The conversation's lossless record: the step log, folding, history tools, previews and the names digest."""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar
from unittest import mock

from frond import cli
from frond.agent.scripted import Step
from frond.agent.session import TurnRecord, format_history, history_preview
from frond.agent.steplog import StepLog, tokens
from frond.events import Compacted, ExecFinished
from tests.helpers import WorkspaceCase, scripted_agent


class StepLogTest(unittest.TestCase):
    def test_records_search_and_survive_a_restart(self):
        path = Path(tempfile.mkdtemp(prefix="frond-log-")) / "s.steps.jsonl"
        log = StepLog(path)
        log.add("user", turn=1, output="make parse_config tolerate tabs")
        seq = log.add(
            "step", turn=1, step=1, reasoning="Read the parser.", code="view('cfg.py')", output="def parseConfig"
        )
        log.add("answer", turn=1, output="done")
        self.assertEqual(seq, 2)
        self.assertEqual(oct(path.stat().st_mode & 0o777), "0o600")
        again = StepLog(path)
        self.assertEqual(len(again), 3)
        record = again.get(2)
        assert record is not None
        self.assertEqual(record.code, "view('cfg.py')")
        hits = again.search("parse config")
        self.assertEqual({h["seq"] for h in hits[:2]}, {1, 2})  # snake_case and camelCase both match
        self.assertEqual(again.add("user", turn=2, output="next"), 4)

    def test_tokens_split_identifiers(self):
        self.assertEqual(
            tokens("parseConfig max_tokens"), ["parseconfig", "parse", "config", "max_tokens", "max", "tokens"]
        )


class FoldingTest(WorkspaceCase):
    def test_folded_steps_stay_recoverable_and_searchable(self):
        steps = [Step("Find the marker.", "print('MARKER-42 ' * 300)")]
        steps += [Step(f"Step {i}.", f"print('{i}' * 900)") for i in range(6)]
        steps.append(
            Step(
                "Recover it.",
                "r = history_step(2); print(r['kind'], r['output'][:16]); print(history_search('MARKER')[0]['seq'])",
            )
        )
        steps.append(Step("Done.", "SUBMIT(response='finished')"))
        agent, engine = scripted_agent(self, steps, max_steps=12)
        agent.window = 1_000  # a tiny window forces folding after a few steps
        record = agent.run_turn("go")
        self.assertEqual(record.response, "finished")
        self.assertTrue(self.of_type(Compacted))
        recovered = [e.output for e in self.of_type(ExecFinished) if "MARKER-42" in (e.output or "")]
        self.assertTrue(any("step MARKER-42 MAR" in o and "\n2" in o for o in recovered), recovered)
        last_prompt = "\n".join(m.text or "" for m in engine.requests[-1].messages)
        self.assertIn("history_step(seq)", last_prompt)
        self.assertIn("· seq 2 · Find the marker.", last_prompt)
        self.assertLess(last_prompt.split("Recover it.")[0].count("MARKER-42"), 20)  # 300 in the step's output

    def test_a_later_turn_finds_an_earlier_turns_steps(self):
        steps = [
            Step("Note the port.", "print('the dev server listens on port 8731')"),
            Step("Done.", "SUBMIT(response='noted')"),
            Step("Look it up.", "print(history_search('dev server port')[0]['match'])"),
            Step("Done.", "SUBMIT(response='found')"),
        ]
        agent, _ = scripted_agent(self, steps)
        agent.run_turn("remember the port")
        agent.run_turn("which port?")
        outputs = [e.output for e in self.of_type(ExecFinished)]
        self.assertTrue(any("listens on port 8731" in (o or "") for o in outputs[2:]), outputs)
        self.assertIn("log seq 1-4", format_history(agent.history))


class PreviewAndNamesTest(WorkspaceCase):
    def test_every_user_message_stays_in_view(self):
        records = [TurnRecord(1, "Never touch the migrations folder.", response="ok " * 5000)]
        records += [TurnRecord(i, f"task {i}", response="done " * 2000) for i in range(2, 6)]
        preview = history_preview(records, format_history(records), 12_000)
        assert preview is not None
        self.assertIn("[turn 1] Never touch the migrations folder.", preview)
        self.assertLessEqual(len(preview), 12_200)

    def test_each_step_lists_the_names_the_code_defined(self):
        steps = [
            Step("Define.", "x = {'a': 1}\ndef helper(path):\n    return path\nbig = 'y' * 100"),
            Step("Done.", "SUBMIT(response='ok')"),
        ]
        agent, engine = scripted_agent(self, steps)
        agent.run_turn("go")
        second = "\n".join(m.text or "" for m in engine.requests[1].messages)
        names = second.split("[[ ## repl_variables ## ]]", 1)[1]
        self.assertIn("x: dict, 1 keys ('a')", names)
        self.assertIn("helper(path): function", names)
        self.assertIn("big: str, 100 chars", names)
        first = "\n".join(m.text or "" for m in engine.requests[0].messages)
        self.assertIn("[[ ## repl_variables ## ]]\n(none yet)", first)


class ContinueKeepsTheLogTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {"notes.txt": "hello\n"}

    def run_cli(self, script: list[dict[str, str]], *args: str) -> str:
        path = self.root / f"script-{len(list(self.root.glob('script-*')))}.json"
        path.write_text(json.dumps(script))
        out = io.StringIO()
        with (
            mock.patch.dict(os.environ, {"XDG_DATA_HOME": str(self.root / "xdg"), "XDG_CACHE_HOME": str(self.root)}),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            cli.main(["-p", "--script", str(path), "-C", str(self.root), *args])
        return out.getvalue().strip()

    def test_continue_can_search_the_earlier_session(self):
        first = [
            {"reasoning": "Measure.", "code": "print('the build takes 93 seconds')"},
            {"reasoning": "Answer.", "code": "SUBMIT(response='measured')"},
        ]
        self.assertEqual(self.run_cli(first, "how long is the build?"), "measured")
        logs = list((self.root / "xdg").rglob("*.steps.jsonl"))
        self.assertEqual(len(logs), 1)
        recall = [{"reasoning": "Look.", "code": "SUBMIT(response=history_search('build seconds')[0]['match'])"}]
        self.assertEqual(self.run_cli(recall, "--continue", "remind me"), "the build takes 93 seconds")


if __name__ == "__main__":
    unittest.main()
