"""The agent session: one conversation, one workspace, one persistent REPL.

``Agent.run_turn`` is blocking and runs on a background thread owned by the caller (the TUI or the
headless runner). Everything the agent does is reported through ``emit``; nothing here knows about
terminals. ``Agent.cancel`` may be called from any thread.
"""

from __future__ import annotations

import atexit
import contextvars
import itertools
import secrets
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

from frond.agent.adapter import FrondAdapter, escape_marker, user_tag
from frond.agent.control import TurnCancelled, TurnControl
from frond.agent.diffing import make_diff
from frond.agent.freshness import Observations
from frond.agent.lm import PROVIDER_ERRORS, build_lm, caches_by_marks, context_window, last_usage, total_cost
from frond.agent.metrics import RunMetrics
from frond.agent.policy import Approver, Mode, Policy
from frond.agent.prompts import CodingTurn, Compaction, Investigation
from frond.agent.repl import ForkRequest, ReplPool
from frond.agent.rlm import Branching, FrondRLM, Hooks
from frond.agent.scopes import ScopeOp, Scopes
from frond.agent.shell import JobManager, ShellRunner
from frond.agent.steplog import StepLog
from frond.agent.streaming import StreamSink, SubmitStreamer
from frond.agent.tools import Delegate, Toolbox
from frond.events import (
    ChangeKind,
    CodeDelta,
    CommandStarted,
    Emit,
    Event,
    ExecFinished,
    ExecOutput,
    ExecStarted,
    FileChanged,
    Folded,
    Notice,
    ReasoningDelta,
    ResponseDelta,
    SteerDelivered,
    SteersReturned,
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
from frond.world import Change, Timeline

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
    effort: str | None = "high"  # the main model's reasoning effort (decision D26); None: the model's default
    sub_effort: str | None = None  # for llm_query sub-calls and sub-agents
    worlds: bool = True  # snapshot the workspace at every step (frond.world): /undo, turn diffs, command diffs
    repl_sandbox: bool = True  # run the REPL worker in the OS sandbox where one works (see ReplSession.start)
    layout: str = "turns"  # how each step sees the history: "turns" (frond) or "chat" (DSPy's stock layout; H6)
    freshness: bool = True  # mark stale reads and refuse overwriting what changed since a read (H3); off: count only
    fork: int = 1  # most branches a FORK may explore (H2); 1 leaves FORK out of the REPL and the prompt
    arm: str = "rlm"  # "rlm": Python in a persistent REPL; "react": one tool call per step, same tools (H1)
    context: str = "fold"  # past the budget: "fold" early steps into a searchable index, or "summary" (H4)
    scopes: bool = False  # scopes as savepoints: open, close (collapse) and abandon (rewind) subtasks (H5)


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
    first_seq: int = 0  # the turn's records in the step log: its message, steps and answer
    last_seq: int = 0
    world_before: str = ""  # the workspace when the turn started and when it ended, as world tree ids
    world_after: str = ""
    head_moved: bool = False  # the turn moved git's HEAD (a commit, a checkout): /undo leaves it to git
    undone: bool = False  # /undo reverted this turn's changes
    error_kind: str = ""  # "provider" when the model provider failed (rate limit, outage, auth), else the type
    steers: list[str] = field(default_factory=list)  # messages the user sent while the turn ran


def _changed(record: TurnRecord) -> bool:
    return bool(record.world_before and record.world_after and record.world_before != record.world_after)


def format_history(records: list[TurnRecord]) -> str:
    parts: list[str] = []
    for r in records:
        parts.append(f"### turn {r.index} · user\n{r.request}")
        parts.extend(f"### turn {r.index} · user (while frond worked)\n{text}" for text in r.steers)
        meta = [r.status, f"{r.steps} step{'s' if r.steps != 1 else ''}"]
        if r.last_seq:
            meta.append(f"log seq {r.first_seq}-{r.last_seq}")
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


MAX_VERBATIM_REQUESTS = 8_000


def history_preview(
    records: list[TurnRecord], formatted: str, limit: int, marker: str = "", searchable: bool = True
) -> str | None:
    """The conversation's preview: every user message verbatim, then as much of the latest turns as fits.

    A summary or a tail-only window drops the user's instructions about how to work far more often than what to
    build (arXiv 2610.31778), so the user's own words always stay in view, and frond's replies give way first.
    With a ``marker``, the user's messages carry its tag and the rest cannot (see adapter.user_tag). ``searchable``:
    the model has history_search (the fold policy).
    """
    if not records:
        return None
    tag = f" {user_tag(marker)}" if marker else ""
    requests: list[str] = []
    for r in records:
        requests.append(f"[turn {r.index}]{tag} {r.request.strip()}")
        requests.extend(f"[turn {r.index}, while frond worked]{tag} {text.strip()}" for text in r.steers)
    shown: list[str] = []
    used = 0
    for text in reversed(requests):
        if used + len(text) > MAX_VERBATIM_REQUESTS and shown:
            break
        shown.insert(0, text)
        used += len(text) + 1
    head = "The user's messages so far, verbatim (oldest first):\n"
    if len(shown) < len(requests):
        where = "`history` and history_search()" if searchable else "`history`"
        head += f"({len(requests) - len(shown)} earlier ones are in {where})\n"
    head += "\n".join(shown)
    room = max(0, limit - len(head) - 80)
    tail = escape_marker(formatted[-room:], marker) if room else ""
    if len(formatted) > room:
        tail = f"… (earlier turns omitted; print(history) for all of them)\n{tail}"
    return f"{head}\n\nThe latest turns:\n{tail}"


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
        self.agent.observations.step = step
        self.agent.emit(StepStarted(step, max_steps))

    def stale_reads(self, step: int) -> str:
        return self.agent.observations.note()

    def fork(self, step: int, request: ForkRequest, branching: Branching) -> str:
        return self.agent._fork(step, request, branching)

    def scope_ops(self) -> list[ScopeOp]:
        return self.agent.scopes.take()

    def open_scopes(self) -> str:
        return self.agent.scopes.describe()

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
        timeline = self.agent.timeline
        self.agent._world = timeline.snapshot() if timeline is not None else ""
        self.agent.emit(ExecFinished(step, output, error, duration, final))
        self.agent.report_confinement()

    def subquery_progress(self, query_id: int, total: int, done: int) -> None:
        self.agent.emit(SubQueryProgress(query_id, total, done))

    def history_budget(self) -> int:
        return self.agent._history_budget()

    def record_step(self, step: int, reasoning: str, code: str, output: str, error: bool) -> int | None:
        turn = self.agent._current.index if self.agent._current else 0
        world, self.agent._world = self.agent._world, ""
        return self.agent.steps.add(
            "step", turn=turn, step=step, reasoning=reasoning, code=code, output=output, error=error, world=world
        )

    def take_messages(self, step: int) -> list[str]:
        return self.agent._take_steers(step)

    def preview(self, name: str, value: Any) -> str | None:
        if name != "history" or not isinstance(value, str):
            return None
        limit = self.agent.rlm.preview_limits.get("history", 12_000)
        return history_preview(self.agent.history, value, limit, self.agent.marker, self.agent.memory is not None)

    def summarize(self, transcript: str) -> str | None:
        return self.agent._summarize(transcript)

    def folded(self, steps: int, before: int, after: int) -> None:
        self.agent.metrics.bump("compactions")
        self.agent.emit(Folded(steps, before, after))

    def code_rejected(self, step: int) -> None:
        self.agent.metrics.bump("syntax_errors")

    def provider_error(self) -> None:
        self.agent.metrics.bump("provider_errors")


class _BranchHooks(Hooks):
    """A FORK branch's loop (ledger B7): its steps are logged and shown under its own card, and it reads its own
    observations; it cannot fork again, steer, or stream into the main transcript."""

    def __init__(self, agent: Agent, branch_id: int, observations: Observations) -> None:
        self.agent = agent
        self.branch_id = branch_id
        self.observations = observations
        self.steps = 0

    def check(self) -> None:
        self.agent.control.check()

    def step_started(self, step: int, max_steps: int) -> None:
        self.steps += 1
        self.observations.step = step
        self.agent.emit(SubAgentProgress(self.branch_id, self.steps, "thinking"))

    def after_lm(self, step: int | None) -> None:
        self.agent._report_usage()

    def step_planned(self, step: int, reasoning: str, code: str) -> None:
        first = next((line.strip() for line in reasoning.splitlines() if line.strip()), "working")
        self.agent.emit(SubAgentProgress(self.branch_id, self.steps, first))

    def history_budget(self) -> int:
        return self.agent._history_budget()

    def summarize(self, transcript: str) -> str | None:
        return self.agent._summarize(transcript)  # within the branch's calls, so its cost is the branch's

    def provider_error(self) -> None:
        self.agent.metrics.bump("provider_errors")

    def folded(self, steps: int, before: int, after: int) -> None:
        self.agent.metrics.bump("compactions")

    def record_step(self, step: int, reasoning: str, code: str, output: str, error: bool) -> int | None:
        turn = self.agent._current.index if self.agent._current else 0
        return self.agent.steps.add(
            "step",
            turn=turn,
            step=step,
            agent=f"branch{self.branch_id}",
            reasoning=reasoning,
            code=code,
            output=output,
            error=error,
        )

    def stale_reads(self, step: int) -> str:
        return self.observations.note()

    def code_rejected(self, step: int) -> None:
        self.agent.metrics.bump("syntax_errors")

    def fork(self, step: int, request: ForkRequest, branching: Branching) -> str:
        return "FORK is not available inside a branch: finish your option, then SUBMIT a report."


@dataclass
class BranchOutcome:
    index: int
    option: str
    world: str  # the workspace the branch left, before its check ran
    steps: int
    submitted: bool  # it called SUBMIT
    passed: bool  # its check exited 0 (with no check: it submitted without error)
    report: str = ""
    error: str = ""
    check_output: str = ""


def _best(outcomes: list[BranchOutcome]) -> BranchOutcome | None:
    passing = [o for o in outcomes if o.passed]
    return min(passing, key=lambda o: (not o.submitted, o.steps, o.index)) if passing else None


def _clip(text: str, limit: int) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _fork_report(
    request: ForkRequest, outcomes: list[BranchOutcome], best: BranchOutcome | None, kept: list[str]
) -> str:
    rule = f"check: {request.check}" if request.check else "no check: a branch that called SUBMIT counts as passing"
    lines = [f"FORK explored {len(outcomes)} options ({rule}):"]
    for o in outcomes:
        state = "passed" if o.passed else "failed"
        ending = "submitted" if o.submitted else f"error: {_clip(o.error, 300)}" if o.error else "ran out of steps"
        line = f"- option {o.index} ({o.option!r}): {state}; {ending} after {o.steps} step(s)."
        if o.report:
            line += f" Its report: {_clip(o.report, 1500)}"
        if request.check and not o.passed and o.check_output:
            line += f" Check output (end): {_clip(o.check_output[-600:], 600)}"
        lines.append(line)
    if best is not None:
        changed = ", ".join(kept) or "no files"
        lines.append(
            f"Kept option {best.index}. The workspace holds its changes ({changed}). The REPL is as it was at FORK: "
            "recompute any value the branch defined."
        )
    else:
        lines.append("No branch passed, so the workspace is as it was at FORK. Choose the next step from the reports.")
    return "\n".join(lines)


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

    def summarize(self, transcript: str) -> str | None:
        return self.agent._summarize(transcript, self.agent.sub_lm)

    def provider_error(self) -> None:
        self.agent.metrics.bump("provider_errors")

    def folded(self, steps: int, before: int, after: int) -> None:
        self.agent.metrics.bump("compactions")

    def record_step(self, step: int, reasoning: str, code: str, output: str, error: bool) -> int | None:
        turn = self.agent._current.index if self.agent._current else 0
        return self.agent.steps.add(
            "step",
            turn=turn,
            step=step,
            agent=f"sub{self.agent_id}",
            reasoning=reasoning,
            code=code,
            output=output,
            error=error,
        )


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
        new_log: Callable[[], Path] | None = None,
        world_dir: Path | None = None,
    ) -> None:
        self.config = config
        self.persist = persist
        self.new_log = new_log  # where a new conversation's step log goes (and, for the caller, its session file)
        self.workspace = workspace
        self._emit = emit
        self.control = TurnControl()
        self.log_dir = Path(tempfile.mkdtemp(prefix="frond-"))
        atexit.register(self.close)
        self.lm = lm or build_lm(config.model, prompt_cache=config.prompt_cache, effort=config.effort)
        self.sub_lm = sub_lm or (
            self.lm
            if config.sub_model == config.model
            else build_lm(config.sub_model, prompt_cache=config.prompt_cache, effort=config.sub_effort)
        )
        self.window: int | None = config.context_window
        # Each step's history is sent as conversation turns, with the latest reply marked for providers that
        # cache only at marked blocks, so every step reads the earlier ones from the provider's cache.
        # Marks the user's messages in the prompt so text from tools, files or answers cannot pass as the user's.
        self.marker = secrets.token_hex(6)
        self._confinement_reported = False
        self.metrics = RunMetrics()  # what the run did, for research exports (ledger B2)
        self.adapter: dspy.ChatAdapter = FrondAdapter(
            cache_breakpoints=config.prompt_cache and caches_by_marks(config.model),
            marker=self.marker,
            metrics=self.metrics,
            layout=config.layout,
            history_tools=config.context == "fold",
        )
        self.sub_adapter: dspy.ChatAdapter = FrondAdapter(
            cache_breakpoints=config.prompt_cache and caches_by_marks(config.sub_model),
            layout=config.layout,
            history_tools=config.context == "fold",
        )
        self.policy = Policy(config.approval, approver)
        self.shell = ShellRunner(workspace.root, self.log_dir, self.emit, self.control.cancelled)
        self.jobs = JobManager(self.log_dir, self.emit)
        self.steps = StepLog()  # every message, step and answer; attach_log() keeps it on disk
        # The step log as the model may search it. The context policy holds for every loop of the turn, the main
        # line, FORK branches and sub-agents alike: under the summary policy nothing can be searched back (H4).
        self.memory = self.steps if config.context == "fold" else None
        # The workspace as a world after every step: whatever changed it is in the difference (frond.world).
        self.timeline = Timeline(workspace.root, world_dir or self.log_dir / "world") if config.worlds else None
        if self.timeline is not None:
            self.timeline.warm()
        self._world = ""  # the world after the latest step, for its step-log record
        self.observations = Observations(workspace.root)  # what the model read this turn (freshness, H3)
        self.scopes = Scopes()  # the open scopes of this turn (H5)
        self._in_branch = False  # a FORK branch runs: scopes belong to the main line
        self.toolbox = Toolbox(
            workspace,
            self.emit,
            shell=self.shell,
            jobs=self.jobs,
            policy=self.policy,
            delegate=Delegate(self._run_subagent, self._run_subagents),
            memory=self.memory,
            timeline=self.timeline,
            metrics=self.metrics,
            observations=self.observations,
            freshness=config.freshness,
        )
        self.pool = ReplPool(
            workspace.root,
            self.control,
            on_output=self._on_exec_output,
            timeout=config.step_timeout,
            policy=config.repl_policy,
            sandbox=config.repl_sandbox,
        )
        self.sink = StreamSink(self.control, self._on_field, self._on_thinking)
        self._submit = SubmitStreamer(lambda text: self.emit(ResponseDelta(text)))
        self.rlm = FrondRLM(
            CodingTurn,
            hooks=_RootHooks(self),
            preview_limits={"request": 20_000, "workspace": 24_000, "history": 12_000, "attachments": 6_000},
            tail_preview=frozenset({"history"}),
            tools=self.toolbox.functions() + (self._scope_tools() if config.scopes else []),
            max_iters=config.max_steps,
            max_llm_calls=config.max_llm_calls,
            max_output_chars=config.max_output_chars,
            sub_lm=self.sub_lm,
            interpreter_factory=self.pool,
            marker=self.marker,
            freshness=config.freshness,
            max_branches=config.fork if config.arm == "rlm" else 1,
            action_space="tools" if config.arm == "react" else "code",
            context=config.context,
            scopes=config.scopes,
        )
        self.pool.root.max_branches = config.fork
        self._listeners = [
            dspy.streaming.StreamListener("code", predict=self.rlm.generate_action, allow_reuse=True),
            dspy.streaming.StreamListener("response", predict=self.rlm.extract, allow_reuse=True),
        ]
        for listener in self._listeners:  # listeners look adapters up by class name; ours speaks ChatAdapter's format
            listener.adapter_identifiers[FrondAdapter.__name__] = listener.adapter_identifiers["ChatAdapter"]
        self.history: list[TurnRecord] = []
        self._turns = itertools.count(1)
        self._subagent_ids = itertools.count(1)
        self._current: TurnRecord | None = None
        self._step = 0
        self._steps_taken = 0
        self._stream_step: int | None = None
        self._thread: threading.Thread | None = None
        self._turn_over = threading.Event()  # set just before a turn emits TurnFinished
        self._steers: list[str] = []  # messages sent while the turn runs, read at the next step boundary
        self._steer_lock = threading.Lock()
        self._accepting_steers = False
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
        previous = self._thread
        if previous is not None and self._turn_over.is_set() and previous is not threading.current_thread():
            # TurnFinished is the last thing a turn emits, so a UI that starts the next queued turn on seeing it
            # can get here before that thread has returned. It is moments from exiting; wait for it.
            previous.join(timeout=2.0)
        if self.busy:
            raise RuntimeError("a turn is already running")
        self._turn_over.clear()
        self._thread = threading.Thread(
            target=self.run_turn, args=(request, attachments or {}), name="frond-turn", daemon=True
        )
        self._thread.start()

    def steer(self, text: str) -> bool:
        """Send a message into the running turn; the model reads it before its next step. False when no turn
        is running (or it is finishing), so the caller should start a turn with it, or queue it."""
        with self._steer_lock:
            if not self._accepting_steers:
                return False
            self._steers.append(text)
            return True

    def _take_steers(self, step: int) -> list[str]:
        with self._steer_lock:
            texts, self._steers = self._steers, []
        record = self._current
        for text in texts:
            if record is not None:
                record.steers.append(text)
                self.steps.add("user", turn=record.index, output=text)
            self.emit(SteerDelivered(text, step))
        return texts

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
        head = ""
        if self.timeline is not None:
            record.world_before, head = self.timeline.begin_turn()
        # the turn's first world goes into the log now, so a collection never takes what it needs (ledger G21)
        record.first_seq = self.steps.add("user", turn=record.index, output=request, world=record.world_before)
        self._current, self._step, self._steps_taken = record, 0, 0
        with self._steer_lock:
            self._steers, self._accepting_steers = [], True
        self.observations.reset()
        self.scopes.reset()
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
            record.error_kind = "provider" if isinstance(exc, PROVIDER_ERRORS) else type(exc).__name__
            if not isinstance(exc, (dspy.LMError, ValueError)):
                self.emit(Notice("error", "".join(traceback.format_exception(exc, limit=-4)).rstrip()))
        finally:
            self._current = None
        with self._steer_lock:  # from here on, a message starts the next turn instead
            unread, self._steers, self._accepting_steers = self._steers, [], False
        if unread:
            self.emit(SteersReturned(tuple(unread)))
        record.steps = self._steps_taken
        record.duration = time.monotonic() - started
        if self.timeline is not None and record.world_before:
            record.world_after = self.timeline.snapshot()
            record.head_moved = self.timeline.head() != head
            # the turn's net change, whoever made it: tools, commands, background jobs (requirement R2)
            if record.world_after:  # "" when snapshots stopped during the turn: no net change can be told
                diff = self.timeline.diff(record.world_before, record.world_after)
                record.files = sorted({c.path for c in diff})
        answer = record.response or record.error or f"(turn {record.status})"
        record.last_seq = self.steps.add("answer", turn=record.index, output=answer, error=record.status == "error")
        self.history.append(record)
        self._save()
        self.workspace.invalidate()
        self._turn_over.set()
        self.emit(
            TurnFinished(record.index, record.response, record.status, record.error, record.duration, record.steps)
        )
        return record

    def _forward(self, inputs: dict[str, Any]) -> dspy.Prediction:
        def work() -> dspy.Prediction:
            with dspy.context(
                lm=self.lm, adapter=self.adapter, send_stream=self.sink, stream_listeners=self._listeners
            ):
                return self.rlm(**inputs)

        async def main() -> dspy.Prediction:
            return await anyio.to_thread.run_sync(work)

        return anyio.run(main)

    def report_confinement(self) -> None:
        """Say once per session when the REPL worker had to run without an OS sandbox, and why."""
        root = self.pool.root
        if self._confinement_reported or root.pid is None or root.confinement or root.unconfined_reason == "turned off":
            return
        self._confinement_reported = True
        self.emit(
            Notice(
                "warn",
                f"The REPL runs without an OS sandbox here ({root.unconfined_reason}). Its Python still holds no "
                "credentials and is kept off the network, commands and files outside temp, but by an audit hook "
                "that code can get around.",
            )
        )

    def _history_budget(self) -> int:
        """Characters of REPL history kept in the prompt before early steps fold (K7, K8)."""
        window = self.window or 200_000
        return int(min(window * 0.45, 150_000) * 3.6)

    def _summarize(self, transcript: str, lm: dspy.LM | None = None) -> str | None:
        """The summary context policy's call (H4): the loop's model (the main one unless ``lm``) condenses the early
        steps of a long turn."""
        try:
            with dspy.context(lm=lm or self.lm, adapter=dspy.ChatAdapter(), send_stream=None):
                prediction = dspy.Predict(Compaction)(transcript=transcript)
        except TurnCancelled:
            raise
        except Exception as exc:
            self.emit(Notice("warn", f"could not summarise earlier steps: {describe_error(exc)}"))
            return None
        self.metrics.bump("summaries")
        return str(prediction.summary or "").strip() or None

    # ── scopes (H5) ──────────────────────────────────────────────────────────

    def _scope_tools(self) -> list[Callable[..., Any]]:
        """The three scope tools, counted like the others (ledger B9)."""

        def open_scope(goal: str) -> str:
            """Start a subtask that will take several steps (reproduce the bug, rewrite parse()). Finish it with
            close_scope(result), or abandon_scope(reason) if the approach fails. Scopes nest."""
            self._outside_branch()
            world = self.timeline.snapshot() if self.timeline is not None else ""
            depth = self.scopes.open(str(goal), self._step, world, list(self.pool.root.names))
            return f"opened scope {depth}: {goal}"

        def close_scope(result: str) -> str:
            """Finish the innermost open scope with its result, as the last call of a step. From the next step its
            steps are one entry in your context, goal and result; they stay in the step log."""
            self._outside_branch()
            scope = self.scopes.end("close", str(result))
            return f"closed scope: {scope.goal}. From the next step its steps are one entry in your context."

        def abandon_scope(reason: str) -> str:
            """Give up the innermost open scope: its workspace changes are reverted, your context goes back to where
            it opened, and your reason stays as a note. REPL variables are not rewound; changed names are listed."""
            self._outside_branch()
            scope = self.scopes.innermost()
            if scope is None:
                raise ValueError("there is no open scope to abandon")
            parts = []
            if self.timeline is not None and scope.world:
                undone = self.timeline.revert(scope.world, self.timeline.snapshot())
                self.workspace.invalidate()
                parts.append(f"Reverted: {', '.join(undone.restored) or 'no files'}.")
                if undone.conflicts:
                    parts.append(f"Kept, since they changed again in the same places: {', '.join(undone.conflicts)}.")
            now = [line for line in self.pool.root.names if line not in scope.names]  # new or changed since
            changed = sorted({line.split(":", 1)[0].split("(", 1)[0].strip() for line in now})
            parts.append(f"REPL names changed since it opened, now stale: {', '.join(changed) or 'none'}.")
            self.scopes.end("abandon", str(reason), " ".join(parts))
            return f"abandoned scope: {scope.goal}. {' '.join(parts)}"

        return [self.metrics.counted(f) for f in (open_scope, close_scope, abandon_scope)]

    def _outside_branch(self) -> None:
        if self._in_branch:
            raise PermissionError("scopes belong to the main line of work; a FORK branch cannot open or end them")

    # ── branches (FORK) ──────────────────────────────────────────────────────

    def _fork(self, step: int, request: ForkRequest, branching: Branching) -> str:
        """Explore a FORK's options, each from the world and REPL at FORK, and keep the best (ledger B7, H2).

        Branches run one after another in the workspace itself, reset to the world at FORK before each, so each
        sees the real directory with its caches and environments (copies would lack the excluded ones). Each runs
        in a fork of the main REPL. The kept branch's world is checked out at the end; with none passing, the world
        at FORK is.
        """
        timeline = self.timeline
        if timeline is None or not timeline.enabled:
            return "FORK needs workspace snapshots, which are off here: choose one option and go on with it."
        start = timeline.snapshot()
        outcomes: list[BranchOutcome] = []
        self._in_branch = True
        try:
            for index, option in enumerate(request.options, start=1):
                self.control.check()
                timeline.work.checkout(start)
                self.workspace.invalidate()
                outcomes.append(self._run_branch(index, len(request.options), option, request, branching))
        except TurnCancelled:
            timeline.work.checkout(start)
            self.workspace.invalidate()
            raise
        finally:
            self._in_branch = False
        best = _best(outcomes)
        timeline.work.checkout(best.world if best is not None else start)
        self.workspace.invalidate()
        self.metrics.forks.append(
            [
                {
                    "option": o.index,
                    "steps": o.steps,
                    "submitted": o.submitted,
                    "passed": o.passed,
                    "kept": o is best,
                    "check": bool(request.check),
                }
                for o in outcomes
            ]
        )
        kept = [c.path for c in timeline.diff(start, best.world)] if best is not None else []
        return _fork_report(request, outcomes, best, kept)

    def _run_branch(
        self, index: int, total: int, option: str, request: ForkRequest, branching: Branching
    ) -> BranchOutcome:
        assert self.timeline is not None
        branch_id = next(self._subagent_ids)
        scope = f"branch{branch_id}"
        self.emit(SubAgentStarted(branch_id, f"branch {index}/{total}: {option}"))
        observations = Observations(self.workspace.root)
        jobs = JobManager(self.log_dir / scope, self.emit)
        toolbox = Toolbox(
            self.workspace,
            self.emit,
            shell=self.shell,
            jobs=jobs,
            policy=self.policy,
            scope=scope,
            memory=self.memory,
            timeline=self.timeline,
            metrics=self.metrics,
            observations=observations,
            freshness=self.config.freshness,
        )
        hooks = _BranchHooks(self, branch_id, observations)
        check = ""
        if request.check:
            check = f" Afterwards frond runs `{request.check}`; a branch whose check passes is kept."
        note = (
            f"[frond] You are branch {index} of {total}. Pursue only this option: {option}\n"
            "The workspace and the REPL are as they were when FORK was called; other branches pursue the other "
            f"options from the same point. You have {request.steps} steps. When you are done, SUBMIT a short "
            f"report of what you did and how you checked it.{check}"
        )
        submitted, report, error, repl = False, "", "", None
        try:
            repl = self.pool.root.fork()
            repl.tools.update({getattr(fn, "__name__", ""): fn for fn in toolbox.functions()})
            first_call = len(self.lm.history)
            try:
                with dspy.context(send_stream=None):
                    result = branching.run(repl, note, request.steps, hooks)
            finally:  # the branch's model calls, so its cost can be told from the main line's (H2)
                for call in range(first_call, len(self.lm.history)):
                    self.metrics.branch_calls[call] = scope
            if isinstance(result, dspy.Prediction):
                submitted, report = True, str(result.get("response") or "")
        except TurnCancelled:
            raise
        except Exception as exc:
            error = describe_error(exc)
        finally:
            jobs.kill_all()
            if repl is not None:
                repl.shutdown()
        world = self.timeline.snapshot()
        passed, check_output = submitted and not error, ""
        if request.check:
            run = self.shell.run(request.check, cwd=self.workspace.root, timeout=self.config.step_timeout, scope=scope)
            passed, check_output = run.ok, run.output
        self.emit(SubAgentFinished(branch_id, _clip(report or error or "(no report)", 400), hooks.steps, passed))
        return BranchOutcome(index, option, world, hooks.steps, submitted, passed, report, error, check_output)

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
            memory=self.memory,
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
            context=self.config.context,
        )
        ok = False
        report = ""
        try:
            with dspy.context(lm=self.sub_lm, adapter=self.sub_adapter, send_stream=None):
                prediction = rlm(task=task, context=context, workspace=self.workspace.snapshot())
            report = str(prediction.report or "").strip()
            ok = True
            return report
        except TurnCancelled:
            report = "(cancelled)"
            raise
        except Exception as exc:
            if isinstance(exc, PROVIDER_ERRORS) and not getattr(exc, "frond_counted", False):
                self.metrics.bump("provider_errors")
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

    # ── housekeeping ─────────────────────────────────────────────────────────

    def undo(self) -> str:
        """Revert the most recent turn that changed files and is not undone yet. Changes made since by anyone else
        stay: undo is a three-way merge of the turn's change against the directory as it is now (requirement R3)."""
        if self.busy:
            raise RuntimeError("stop the current turn before undoing")
        timeline = self.timeline
        if timeline is None or not timeline.enabled:
            reason = timeline.reason if timeline is not None else "worlds are switched off"
            return f"nothing to undo: workspace snapshots are off ({reason})"
        target = next((r for r in reversed(self.history) if _changed(r) and not r.undone), None)
        if target is None:
            return "nothing to undo: no turn has changed files"
        if target.head_moved:
            return (
                f"turn {target.index} moved git's HEAD (a commit or a checkout), so its file changes are not undone "
                "here: undo the commit with git"
            )
        current = timeline.snapshot()
        result = timeline.revert(target.world_before, target.world_after)
        for change in timeline.diff(current, timeline.snapshot()):
            self._emit(self._change_event(change, scope="undo"))
        target.undone = True
        self.workspace.invalidate()
        summary = f"reverted the file changes of turn {target.index}: {', '.join(result.restored) or 'no files'}"
        if result.conflicts:
            summary += f"; kept {', '.join(result.conflicts)} as they are, since they changed again in the same places"
        if result.unrestorable:
            summary += f"; could not restore {', '.join(result.unrestorable)} (too large to have been kept)"
        self.history.append(TurnRecord(next(self._turns), "/undo", f"(the user {summary})", "done"))
        self._save()
        return summary

    def turn_diff(self, index: int | None = None) -> list[FileChanged]:
        """A turn's net change as diffs, the latest turn that changed files when ``index`` is None (R2)."""
        turns = [r for r in self.history if _changed(r) and (index is None or r.index == index)]
        if self.timeline is None or not turns:
            return []
        changes = self.timeline.diff(turns[-1].world_before, turns[-1].world_after)
        return [self._change_event(c, scope="diff") for c in changes]

    def _change_event(self, change: Change, *, scope: str) -> FileChanged:
        timeline = self.timeline
        assert timeline is not None
        kind: ChangeKind = "create" if change.before is None else "delete" if change.after is None else "edit"
        if any(e is not None and e.kind != "file" for e in (change.before, change.after)):
            kinds = " → ".join(e.kind if e is not None else "absent" for e in (change.before, change.after))
            return FileChanged(change.path, kind, f"({kinds})", 0, 0, scope=scope)
        old_bytes, new_bytes = timeline.content(change.before) or b"", timeline.content(change.after) or b""
        before, after = change.before, change.after
        mode = f"(mode {before.mode:o} → {after.mode:o})" if before and after and before.mode != after.mode else ""
        if b"\0" in old_bytes or b"\0" in new_bytes:
            return FileChanged(change.path, kind, "\n".join(filter(None, ["(binary file)", mode])), 0, 0, scope=scope)
        old, new = old_bytes.decode("utf-8", errors="replace"), new_bytes.decode("utf-8", errors="replace")
        diff = make_diff(old, new, change.path, created=kind == "create", deleted=kind == "delete")
        text = "\n".join(filter(None, [diff.text if old != new else "", mode]))  # a chmod alone shows (F15)
        return FileChanged(change.path, kind, text, diff.added, diff.removed, scope=scope)

    def attach_log(self, path: Path) -> None:
        """Keep the step log in ``path`` (beside the session file), loading what an earlier session recorded."""
        self.steps.attach(path)

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
        """Start a new conversation (the REPL namespace is kept unless reset_repl is called). The old conversation's
        steps stay in their file, out of history_search; with no ``new_log`` the new record is kept in memory only."""
        self.history.clear()
        self.steps.restart(self.new_log() if self.new_log is not None else None)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.control.cancel()
        self.shell.kill_all()
        self.jobs.kill_all()
        self.pool.close()
        shutil.rmtree(self.log_dir, ignore_errors=True)
