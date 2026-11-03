"""Conversation persistence (--continue), in-turn compaction, and the workspace snapshot."""

import contextlib
import io
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import ClassVar
from unittest import mock

from frond import cli
from frond.agent.scripted import Step
from frond.agent.session import TurnRecord
from frond.events import Folded
from frond.sessions import SessionStore
from frond.workspace import Workspace
from tests.helpers import WorkspaceCase, scripted_agent


class SessionStoreTest(WorkspaceCase):
    def test_round_trip_and_latest(self):
        store = SessionStore(self.root, base=self.root / "data")
        self.assertIsNone(store.latest())
        path = store.new_path()
        records = [TurnRecord(1, "hi", "hello", "done", 2, 1.5, ["a.py"], ["ls"])]
        store.save(path, records, "test/model")
        self.assertEqual(store.latest(), path)
        self.assertEqual(store.load(path), records)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_agent_persists_after_each_turn_and_restores(self):
        saved: list[list[TurnRecord]] = []
        agent, _ = scripted_agent(self, [Step("Hi.", "SUBMIT(response='first')")])
        agent.persist = lambda records: saved.append(list(records))
        agent.run_turn("one")
        self.assertEqual([r.response for r in saved[-1]], ["first"])
        agent.restore([TurnRecord(7, "old question", "old answer")])
        record = agent.run_turn("next")
        self.assertEqual(record.index, 8)


class ContinueCliTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {"notes.txt": "hello\n"}

    def run_cli(self, script: list[dict[str, str]], *args: str) -> tuple[int, str]:
        path = self.root / f"script-{len(list(self.root.glob('script-*')))}.json"
        path.write_text(json.dumps({"steps": script}))
        out = io.StringIO()
        with (
            mock.patch.dict(os.environ, {"XDG_DATA_HOME": str(self.root / "xdg"), "XDG_CACHE_HOME": str(self.root)}),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            code = cli.main(["-p", "--script", str(path), "-C", str(self.root), *args])
        return code, out.getvalue()

    def test_continue_brings_back_the_conversation(self):
        code, out = self.run_cli([{"reasoning": "Answer.", "code": "SUBMIT(response='the answer is 42')"}], "question")
        self.assertEqual((code, out.strip()), (0, "the answer is 42"))
        recall = [{"reasoning": "Look back.", "code": "SUBMIT(response=str('42' in history))"}]
        _, out = self.run_cli(recall, "--continue", "what was it?")
        self.assertEqual(out.strip(), "True")
        _, out = self.run_cli(recall, "a fresh start")
        self.assertEqual(out.strip(), "False")


class CompactionTest(WorkspaceCase):
    def test_long_turns_compact_old_steps_and_keep_going(self):
        steps = [Step(f"Step {i}.", f"print('{i}' * 400)") for i in range(7)]
        steps.append(Step("Done.", "SUBMIT(response='finished')"))
        agent, _ = scripted_agent(self, steps, max_steps=12, sub_answer=lambda prompt: "summary of the early steps")
        agent.window = 1_000  # a tiny window forces compaction after a few steps
        record = agent.run_turn("go")
        self.assertEqual(record.response, "finished")
        compactions = [e for e in self.events if isinstance(e, Folded)]
        self.assertTrue(compactions)
        self.assertLess(compactions[-1].after_chars, compactions[-1].before_chars)


class WorkspaceSnapshotTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {"AGENTS.md": "Always run `make check`.\n", "uv.lock": "", "src/main.py": ""}

    def test_snapshot_includes_instructions_git_and_tooling(self):
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        ws = Workspace(self.root)
        snapshot = ws.snapshot()
        self.assertIn("Always run `make check`.", snapshot)
        self.assertIn("uv project", snapshot)
        self.assertIn("git: branch", snapshot)
        self.assertIn("src/main.py", ws.files())
        with tempfile.TemporaryDirectory() as config:
            Path(config, "frond").mkdir()
            Path(config, "frond", "AGENTS.md").write_text("Prefer short answers.\n")
            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": config}):
                self.assertIn("Prefer short answers.", ws.snapshot())
