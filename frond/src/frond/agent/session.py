"""The agent session: one conversation, one workspace, one persistent REPL.

``Agent.run_turn`` is blocking and runs on a background thread owned by the caller (the TUI or the
headless runner). Everything the agent does is reported through ``emit``; nothing here knows about
terminals. ``Agent.cancel`` may be called from any thread.
"""

from __future__ import annotations

import atexit
import contextvars
import itertools
import shutil
import tempfile
import threading
import time
import traceback
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import anyio
import dspy

from frond.agent.checkpoints import Checkpoints
from frond.agent.control import TurnCancelled, TurnControl
from frond.agent.diffing import make_diff
from frond.agent.lm import build_lm, context_window, last_usage, total_cost
from frond.agent.policy import Approver, Mode, Policy
from frond.agent.prompts import CodingTurn, Investigation
from frond.agent.repl import ReplPool
from frond.agent.rlm import FrondRLM, Hooks
from frond.agent.shell import JobManager, ShellRunner
from frond.agent.streaming import StreamSink, SubmitStreamer
from frond.agent.tools import Delegate, Toolbox
from frond.events import (
    ChangeKind,
    CodeDelta,
    CommandStarted,
    Compacted,
    Emit,
    Event,
    ExecFinished,
    ExecOutput,
    ExecStarted,
    FileChanged,
    Notice,
    ReasoningDelta,
    ResponseDelta,
    StepPlanned,
    StepStarted,
    SubAgentFinished,
    SubAgentProgress,
    SubAgentStarted,
    SubQueryProgress,
    ThinkingDelta,
    TurnFinished,
    TurnStarted,
    TurnStatus,
    UsageUpdated,
)
from frond.workspace import Workspace

MAX_ATTACHMENT_CHARS = 120_000


@dataclass
class AgentConfig:
    model: str
    sub_model: str
    max_steps: int = 40
    max_llm_calls: int = 80
    step_timeout: float = 600.0
    approval: Mode = "auto"
    repl_policy: str = "strict"
    max_output_chars: int = 16_000
    subagent_steps: int = 16
    context_window: int | None = None
    prompt_cache: bool = True


@dataclass
class TurnRecord:
    index: int
    request: str
    response: str = ""
    status: TurnStatus = "done"
    steps: int = 0
    duration: float = 0.0
    files: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    error: str | None = None


def format_history(records: list[TurnRecord]) -> str:
    parts: list[str] = []
    for r in records:
        parts.append(f"### turn {r.index} · user\n{r.request}")
        meta = [r.status, f"{r.steps} step{'s' if r.steps != 1 else ''}"]
        if r.files:
            files = ", ".join(dict.fromkeys(r.files))
            meta.append(f"changed {files[:400]}")
        if r.commands:
            meta.append("ran " + "; ".join(f"`{c[:80]}`" for c in r.commands[-5:]))
        reply = r.response or {
            "cancelled": "(stopped by the user before finishing)",
            "error": f"(failed: {r.error})",
        }.get(r.status, "(no reply)")
        parts.append(f"### turn {r.index} · frond ({' · '.join(meta)})\n{reply}")
    return "\n\n".join(parts)


def describe_error(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    lowered = text.lower()
    if "to fix" in lowered:
        return text  # the LM layer already explained the remedy
    if "auth" in lowered or "api key" in lowered or "401" in lowered:
        text += "\nCheck that the API key for this provider is set and valid."
    elif "rate" in lowered and "limit" in lowered:
        text += "\nThe provider is rate-limiting requests; wait a moment and try again."
    return text


class _RootHooks(Hooks):
    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    def check(self) -> None:
        self.agent.control.check()

    def step_started(self, step: int, max_steps: int) -> None:
        self.agent._step = step
        self.agent._steps_taken = step
        self.agent.emit(StepStarted(step, max_steps))

    def before_lm(self, step: int | None) -> None:
        self.agent._stream_step = step
        self.agent._submit.reset()
        self.agent.sink.arm()

    def after_lm(self, step: int | None) -> None:
        self.agent._report_usage()

    def step_planned(self, step: int, reasoning: str, code: str) -> None:
        self.agent.emit(StepPlanned(step, reasoning, code))

    def exec_started(self, step: int) -> None:
        self.agent.emit(ExecStarted(step))

    def exec_finished(self, step: int, output: str, error: str | None, duration: float, final: bool) -> None:
        self.agent.emit(ExecFinished(step, output, error, duration, final))

    def subquery_progress(self, query_id: int, total: int, done: int) -> None:
        self.agent.emit(SubQueryProgress(query_id, total, done))

    def history_budget(self) -> int:
        window = self.agent.window or 200_000
        return int(min(window * 0.45, 150_000) * 3.6)

    def summarize(self, text: str) -> str | None:
        return self.agent._summarize(text)

    def compacted(self, steps: int, before: int, after: int) -> None:
        self.agent.emit(Compacted(steps, before, after))


class _SubHooks(Hooks):
    def __init__(self, agent: Agent, agent_id: int) -> None:
        self.agent = agent
        self.agent_id = agent_id
        self.steps = 0

    def check(self) -> None:
        self.agent.control.check()

    def step_started(self, step: int, max_steps: int) -> None:
        self.steps = step
        self.agent.emit(SubAgentProgress(self.agent_id, step, "thinking"))

    def step_planned(self, step: int, reasoning: str, code: str) -> None:
        first = next((line.strip() for line in reasoning.splitlines() if line.strip()), "working")
        self.agent.emit(SubAgentProgress(self.agent_id, step, first))


class Agent:
    def __init__(
        self,
        config: AgentConfig,
        workspace: Workspace,
        emit: Emit,
        *,
        approver: Approver | None = None,
        lm: dspy.LM | None = None,
        sub_lm: dspy.LM | None = None,
        persist: Callable[[list[TurnRecord]], None] | None = None,
    ) -> None:
        self.config = config
        self.persist = persist
        self.workspace = workspace
        self._emit = emit
        self.control = TurnControl()
        self.log_dir = Path(tempfile.mkdtemp(prefix="frond-"))
        atexit.register(self.close)
        self.lm = lm or build_lm(config.model, prompt_cache=config.prompt_cache)
        self.sub_lm = sub_lm or (
            self.lm
            if config.sub_model == config.model
            else build_lm(config.sub_model, prompt_cache=config.prompt_cache)
        )
        self.window: int | None = config.context_window
        self.policy = Policy(config.approval, approver)
        self.shell = ShellRunner(workspace.root, self.log_dir, self.emit, self.control.cancelled)
        self.jobs = JobManager(self.log_dir, self.emit)
        self.checkpoints = Checkpoints()
        self.toolbox = Toolbox(
            workspace,
            self.emit,
            shell=self.shell,
            jobs=self.jobs,
            policy=self.policy,
            delegate=Delegate(self._run_subagent, self._run_subagents),
            checkpoints=self.checkpoints,
        )
        self.pool = ReplPool(
            workspace.root,
            self.control,
            on_output=self._on_exec_output,
            timeout=config.step_timeout,
            policy=config.repl_policy,
        )
        self.sink = StreamSink(self.control, self._on_field, self._on_thinking)
        self._submit = SubmitStreamer(lambda text: self.emit(ResponseDelta(text)))
        self.rlm = FrondRLM(
            CodingTurn,
            hooks=_RootHooks(self),
            preview_limits={"request": 20_000, "workspace": 24_000, "history": 12_000, "attachments": 6_000},
            tail_preview=frozenset({"history"}),
            tools=self.toolbox.functions(),
            max_iters=config.max_steps,
            max_llm_calls=config.max_llm_calls,
            max_output_chars=config.max_output_chars,
            sub_lm=self.sub_lm,
            interpreter_factory=self.pool,
        )
        self._listeners = [
            dspy.streaming.StreamListener("code", predict=self.rlm.generate_action, allow_reuse=True),
            dspy.streaming.StreamListener("response", predict=self.rlm.extract, allow_reuse=True),
        ]
        self.history: list[TurnRecord] = []
        self._turns = itertools.count(1)
        self._subagent_ids = itertools.count(1)
        self._current: TurnRecord | None = None
        self._step = 0
        self._steps_taken = 0
        self._stream_step: int | None = None
        self._thread: threading.Thread | None = None
        self._closed = False
        if self.window is None:  # started last: the lookup thread reports through emit(), which needs the above
            threading.Thread(target=self._lookup_window, name="frond-window", daemon=True).start()

    # ── event plumbing ───────────────────────────────────────────────────────

    def emit(self, event: Event) -> None:
        record = self._current
        if record is not None:
            if isinstance(event, FileChanged) and not event.scope:
                record.files.append(event.path)
            elif isinstance(event, CommandStarted) and not event.scope:
                record.commands.append(event.command)
        self._emit(event)

    def _on_field(self, name: str, text: str) -> None:
        step = self._stream_step
        if name == "reasoning" and step is not None:
            self.emit(ReasoningDelta(step, text))
        elif name == "code" and step is not None:
            self.emit(CodeDelta(step, text))
            self._submit.feed(text)
        elif name == "response":
            self.emit(ResponseDelta(text))

    def _on_thinking(self, text: str) -> None:
        self.emit(ThinkingDelta(self._stream_step or 0, text))

    def _on_exec_output(self, text: str) -> None:
        self.emit(ExecOutput(self._step, text))

    def _lookup_window(self) -> None:
        self.window = context_window(self.config.model)
        self._report_usage()

    def _report_usage(self) -> None:
        prompt, completion, cached = last_usage(self.lm)
        self.emit(
            UsageUpdated(self.config.model, prompt, completion, self.window, total_cost(self.lm, self.sub_lm), cached)
        )

    # ── turns ────────────────────────────────────────────────────────────────

    @property
    def busy(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start_turn(self, request: str, attachments: dict[str, str] | None = None) -> None:
        """Run a turn on a background thread. Raises RuntimeError if one is already running."""
        if self.busy:
            raise RuntimeError("a turn is already running")
        self._thread = threading.Thread(
            target=self.run_turn, args=(request, attachments or {}), name="frond-turn", daemon=True
        )
        self._thread.start()

    def cancel(self) -> None:
        if self.busy:
            self.control.cancel()
            self.shell.kill_all()

    def wait(self, timeout: float | None = None) -> bool:
        thread = self._thread
        if thread is not None:
            thread.join(timeout)
            return not thread.is_alive()
        return True

    def run_turn(self, request: str, attachments: dict[str, str] | None = None) -> TurnRecord:
        attachments = attachments or {}
        self.control.reset()
        record = TurnRecord(next(self._turns), request)
        self._current, self._step, self._steps_taken = record, 0, 0
        self.checkpoints.begin(record.index)
        started = time.monotonic()
        self.emit(TurnStarted(record.index, request, tuple(attachments)))
        inputs = {
            "request": request,
            "history": format_history(self.history),
            "workspace": self.workspace.snapshot(),
            "attachments": {k: v[:MAX_ATTACHMENT_CHARS] for k, v in attachments.items()},
        }
        try:
            prediction = self._forward(inputs)
            record.response = str(prediction.response or "").strip()
            record.status = "limit" if prediction.get("final_reasoning") == "Extract forced final output" else "done"
        except TurnCancelled:
            record.status = "cancelled"
        except Exception as exc:
            record.status, record.error = "error", describe_error(exc)
            if not isinstance(exc, (dspy.LMError, ValueError)):
                self.emit(Notice("error", "".join(traceback.format_exception(exc, limit=-4)).rstrip()))
        finally:
            self._current = None
        record.steps = self._steps_taken
        record.duration = time.monotonic() - started
        self.history.append(record)
        self._save()
        self.workspace.invalidate()
        self.emit(
            TurnFinished(record.index, record.response, record.status, record.error, record.duration, record.steps)
        )
        return record

    def _forward(self, inputs: dict[str, Any]) -> dspy.Prediction:
        def work() -> dspy.Prediction:
            with dspy.context(lm=self.lm, send_stream=self.sink, stream_listeners=self._listeners):
                return self.rlm(**inputs)

        async def main() -> dspy.Prediction:
            return await anyio.to_thread.run_sync(work)

        return anyio.run(main)

    # ── sub-agents ───────────────────────────────────────────────────────────

    def _run_subagent(self, task: str, context: str = "") -> str:
        agent_id = next(self._subagent_ids)
        scope = f"sub{agent_id}"
        self.emit(SubAgentStarted(agent_id, task))
        hooks = _SubHooks(self, agent_id)
        toolbox = Toolbox(
            self.workspace,
            self.emit,
            shell=self.shell,
            jobs=self.jobs,
            policy=self.policy,
            scope=scope,
            read_only=True,
        )
        rlm = FrondRLM(
            Investigation,
            hooks=hooks,
            preview_limits={"task": 8_000, "context": 8_000, "workspace": 16_000},
            tools=toolbox.functions(),
            max_iters=self.config.subagent_steps,
            max_llm_calls=40,
            max_output_chars=self.config.max_output_chars,
            sub_lm=self.sub_lm,
            interpreter_factory=self.pool.ephemeral,
        )
        ok = False
        report = ""
        try:
            with dspy.context(lm=self.sub_lm, send_stream=None):
                prediction = rlm(task=task, context=context, workspace=self.workspace.snapshot())
            report = str(prediction.report or "").strip()
            ok = True
            return report
        except TurnCancelled:
            report = "(cancelled)"
            raise
        except Exception as exc:
            report = f"sub-agent failed: {describe_error(exc)}"
            raise RuntimeError(report) from exc
        finally:
            self.emit(SubAgentFinished(agent_id, report, hooks.steps, ok))

    def _run_subagents(self, tasks: list[str]) -> list[str]:
        if not tasks:
            return []
        with ThreadPoolExecutor(max_workers=min(4, len(tasks)), thread_name_prefix="frond-sub") as pool:
            futures = [pool.submit(contextvars.copy_context().run, self._safe_subagent, t) for t in tasks]
            return [f.result() for f in futures]

    def _safe_subagent(self, task: str) -> str:
        try:
            return self._run_subagent(task)
        except TurnCancelled:
            raise
        except Exception as exc:
            return f"[ERROR] {exc}"

    def _summarize(self, transcript: str) -> str | None:
        prompt = (
            "Summarise these earlier steps of a coding agent's work so it can continue without them. Keep every "
            "concrete fact it will need: files read or changed (with line numbers), commands run and their results, "
            "errors seen, decisions made, and what remains to do. Be terse.\n\n" + transcript[-200_000:]
        )
        try:
            with dspy.context(send_stream=None):
                out = self.sub_lm(prompt)
            first = out[0] if isinstance(out, list) and out else out
            text = first.get("text") if isinstance(first, dict) else first
            return str(text) if text else None
        except Exception:
            return None

    # ── housekeeping ─────────────────────────────────────────────────────────

    def undo(self) -> str:
        """Restore the files changed by the most recent turn that changed any. Returns a summary."""
        if self.busy:
            raise RuntimeError("stop the current turn before undoing")
        result = self.checkpoints.undo()
        if result is None:
            return "nothing to undo: no turn has changed files through frond's tools"
        checkpoint, restored = result
        for item in restored:
            display = self.workspace.rel(item.path)
            if item.moved_from is not None:
                self._emit(
                    FileChanged(display, "move", "", 0, 0, old_path=self.workspace.rel(item.moved_from), scope="undo")
                )
                continue
            old = (item.before or b"").decode("utf-8", errors="replace")
            new = (item.after or b"").decode("utf-8", errors="replace")
            kind: ChangeKind = "delete" if item.after is None else "create" if item.before is None else "edit"
            diff = make_diff(old, new, display, created=item.before is None, deleted=item.after is None)
            self._emit(FileChanged(display, kind, diff.text, diff.added, diff.removed, scope="undo"))
        self.workspace.invalidate()
        paths = ", ".join(self.workspace.rel(r.path) for r in restored) or "no files"
        summary = f"reverted the file changes of turn {checkpoint.turn}: {paths}"
        if checkpoint.lost:
            summary += f" (could not restore: {', '.join(checkpoint.lost)})"
        self.history.append(TurnRecord(next(self._turns), "/undo", f"(the user {summary})", "done"))
        self._save()
        return summary

    def restore(self, records: list[TurnRecord]) -> None:
        """Continue an earlier conversation: the agent sees its turns (the REPL starts fresh)."""
        self.history = list(records)
        self._turns = itertools.count(max((r.index for r in records), default=0) + 1)

    def _save(self) -> None:
        if self.persist is not None:
            try:
                self.persist(self.history)
            except Exception as exc:  # never lose a turn's result over a disk problem
                self._emit(Notice("warn", f"could not save the session: {exc}"))

    def reset_repl(self) -> None:
        self.pool.reset()

    def clear(self) -> None:
        """Forget the conversation (the REPL namespace is kept unless reset_repl is called)."""
        self.history.clear()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.control.cancel()
        self.shell.kill_all()
        self.jobs.kill_all()
        self.pool.close()
        shutil.rmtree(self.log_dir, ignore_errors=True)
