"""Shared fixtures: temporary workspaces, a toolbox wired to an event list, scripted agents."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar

from frond.agent.control import TurnControl
from frond.agent.policy import Approver, Mode, Policy
from frond.agent.scripted import ScriptedEngine, Step, scripted_lm
from frond.agent.session import Agent, AgentConfig
from frond.agent.shell import JobManager, ShellRunner
from frond.agent.tools import Toolbox
from frond.events import Event
from frond.workspace import Workspace


class WorkspaceCase(unittest.TestCase):
    files: ClassVar[dict[str, str]] = {}

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="frond-test-"))
        for name, text in self.files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        self.ws = Workspace(self.root)
        self.events: list[Event] = []
        self.addCleanup(shutil.rmtree, self.root, True)

    def toolbox(
        self,
        *,
        mode: Mode = "auto",
        approver: Approver | None = None,
        read_only: bool = False,
        control: TurnControl | None = None,
    ) -> Toolbox:
        control = control or TurnControl()
        logs = Path(tempfile.mkdtemp(prefix="frond-logs-"))
        self.addCleanup(shutil.rmtree, logs, True)
        shell = ShellRunner(self.root, logs, self.events.append, control.cancelled)
        jobs = JobManager(logs, self.events.append)
        self.addCleanup(jobs.kill_all)
        return Toolbox(
            self.ws, self.events.append, shell=shell, jobs=jobs, policy=Policy(mode, approver), read_only=read_only
        )

    def of_type(self, kind: type) -> list:
        return [e for e in self.events if isinstance(e, kind)]


def scripted_agent(
    case: WorkspaceCase,
    steps: list[Step],
    *,
    delay: float = 0.0,
    max_steps: int = 10,
    sub_answer=None,
    approver: Approver | None = None,
) -> tuple[Agent, ScriptedEngine]:
    engine = ScriptedEngine(steps, chunk=5, delay=delay, sub_answer=sub_answer)
    lm = scripted_lm(engine)
    config = AgentConfig(
        model="openai/frond-scripted", sub_model="openai/frond-scripted", max_steps=max_steps, context_window=100_000
    )
    agent = Agent(config, case.ws, case.events.append, approver=approver, lm=lm, sub_lm=lm)
    case.addCleanup(agent.close)
    return agent, engine
