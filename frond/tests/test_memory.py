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
from frond.events import ExecFinished, Folded
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

    def test_a_line_cut_short_by_a_crash_does_not_swallow_the_next_record(self):
        path = Path(tempfile.mkdtemp(prefix="frond-log-")) / "s.steps.jsonl"
        StepLog(path).add("user", turn=1, output="first")
        with open(path, "a", encoding="utf-8") as f:
            f.write('{"seq": 2, "kind": "step", "turn": 1, "out')  # the process died mid-write
        log = StepLog(path)
        self.assertEqual(len(log), 1)
        log.add("answer", turn=1, output="after the crash")
        again = StepLog(path)
        self.assertEqual([r.output for r in again.records()], ["first", "after the crash"])

    def test_a_restart_begins_a_new_record_and_keeps_the_old_file(self):
        directory = Path(tempfile.mkdtemp(prefix="frond-log-"))
        log = StepLog(directory / "a.steps.jsonl")
        log.add("user", turn=1, output="the build takes 93 seconds")
        log.restart(directory / "b.steps.jsonl")
        self.assertEqual((len(log), log.search("build seconds")), (0, []))
        self.assertEqual(log.add("user", turn=1, output="a new conversation"), 1)
        self.assertEqual(len(StepLog(directory / "a.steps.jsonl")), 1)
        self.assertEqual(len(StepLog(directory / "b.steps.jsonl")), 1)

    def test_a_log_written_before_the_rename_still_loads(self):
        path = Path(tempfile.mkdtemp(prefix="frond-log-")) / "s.steps.jsonl"
        path.write_text('{"seq": 1, "kind": "step", "turn": 1, "step": 1, "scope": "sub2", "output": "old"}\n')
        record = StepLog(path).get(1)
        assert record is not None
        self.assertEqual((record.agent, record.output), ("sub2", "old"))

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
        self.assertTrue(self.of_type(Folded))
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

    def test_code_that_does_not_compile_leaves_the_names_as_they_were(self):
        steps = [
            Step("Define.", "x = {'a': 1}"),
            Step("Typo.", "def broken(:"),
            Step("Done.", "SUBMIT(response='ok')"),
        ]
        agent, engine = scripted_agent(self, steps)
        agent.run_turn("go")
        third = "\n".join(m.text or "" for m in engine.requests[2].messages)
        self.assertIn("x: dict, 1 keys ('a')", third.split("[[ ## repl_variables ## ]]", 1)[1])


class NewConversationTest(WorkspaceCase):
    def test_a_new_conversation_cannot_search_the_old_one(self):
        directory = Path(tempfile.mkdtemp(prefix="frond-log-"))
        steps = [
            Step("Measure.", "print('the build takes 93 seconds')"),
            Step("Answer.", "SUBMIT(response='measured')"),
            Step("Recall.", "SUBMIT(response=repr(history_search('build seconds')))"),
        ]
        agent, _ = scripted_agent(self, steps)
        agent.attach_log(directory / "old.steps.jsonl")
        agent.new_log = lambda: directory / "new.steps.jsonl"
        agent.run_turn("how long is the build?")
        agent.clear()
        self.assertEqual(agent.run_turn("what did we measure?").response, "[]")
        self.assertIn("93 seconds", (directory / "old.steps.jsonl").read_text())
        self.assertNotIn("93 seconds", (directory / "new.steps.jsonl").read_text())


class NarrowingHintTest(WorkspaceCase):
    """A cut output says how to see the rest or narrow it (B14; TurnCost: 76.9% against 44% without)."""

    def test_a_long_output_points_at_its_record_and_at_narrower_code(self):
        steps = [Step("Dump.", "print('x' * 40_000)"), Step("Done.", "SUBMIT(response='ok')")]
        agent, engine = scripted_agent(self, steps)
        agent.run_turn("dump")
        second = "\n".join(m.text or "" for m in engine.requests[1].messages)
        self.assertIn("characters omitted; history_step(2) shows all of it; next time print a slice", second)

    def test_the_summary_arm_has_no_history_step_to_point_at(self):
        steps = [Step("Dump.", "print('x' * 40_000)"), Step("Done.", "SUBMIT(response='ok')")]
        agent, engine = scripted_agent(self, steps, context="summary")
        agent.run_turn("dump")
        second = "\n".join(m.text or "" for m in engine.requests[1].messages)
        self.assertIn("characters omitted; next time print a slice", second)


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

    def test_export_writes_the_runs_record(self):
        export = self.root / "out"
        script = [
            {"reasoning": "Look.", "code": "print('looked')"},
            {"reasoning": "Answer.", "code": "SUBMIT(response='exported')"},
        ]
        self.assertEqual(self.run_cli(script, "--export", str(export), "go"), "exported")
        records = [json.loads(line) for line in (export / "steps.jsonl").read_text().splitlines()]
        self.assertEqual([r["kind"] for r in records], ["user", "step", "step", "answer"])
        self.assertEqual(records[1]["output"].strip(), "looked")
        usage = json.loads((export / "usage.json").read_text())
        self.assertEqual(usage["calls"], 2)
        self.assertGreater(usage["input_tokens"], 0)
        self.assertEqual((export / "answer.md").read_text(), "exported")

    def test_a_continued_run_exports_only_what_it_did(self):
        first = [
            {"reasoning": "Look.", "code": "print('looked')"},
            {"reasoning": "Answer.", "code": "SUBMIT(response='first')"},
        ]
        self.assertEqual(self.run_cli(first, "go"), "first")
        export = self.root / "out"
        second = [{"reasoning": "Answer.", "code": "SUBMIT(response='second')"}]
        self.assertEqual(self.run_cli(second, "--continue", "--export", str(export), "again"), "second")
        records = [json.loads(line) for line in (export / "steps.jsonl").read_text().splitlines()]
        self.assertEqual([r["kind"] for r in records], ["user", "step", "answer"])
        metrics = json.loads((export / "metrics.json").read_text())
        self.assertEqual((metrics["turns"], metrics["steps"], metrics["continued_after_seq"]), (1, 1, 4))
        self.assertEqual(json.loads((export / "usage.json").read_text())["calls"], 1)

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
