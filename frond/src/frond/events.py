"""Events flowing from the agent thread to whatever renders it (the TUI, the headless printer, tests).

Every event is an immutable value. The agent never touches the UI; it only emits these. That one-way
edge is what makes the agent testable without a terminal and the UI testable without a model.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

type Scope = str  # "" for the root agent, "sub1", "sub2", ... for sub-agents
type CommandStatus = Literal["ok", "failed", "timeout", "cancelled", "background"]
type TurnStatus = Literal["done", "cancelled", "error", "limit"]
type ChangeKind = Literal["create", "edit", "delete", "move"]
type PlanStatus = Literal["done", "active", "todo"]


@dataclass(frozen=True, slots=True)
class TurnStarted:
    turn: int
    request: str
    attachments: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StepStarted:
    step: int
    max_steps: int


@dataclass(frozen=True, slots=True)
class ReasoningDelta:
    step: int
    text: str


@dataclass(frozen=True, slots=True)
class CodeDelta:
    step: int
    text: str


@dataclass(frozen=True, slots=True)
class ThinkingDelta:
    step: int
    text: str


@dataclass(frozen=True, slots=True)
class ResponseDelta:
    """Text of the final answer, streamed while the model is still writing its SUBMIT(...) call."""

    text: str


@dataclass(frozen=True, slots=True)
class StepPlanned:
    """The parsed action for a step: what the model decided after streaming finished."""

    step: int
    reasoning: str
    code: str


@dataclass(frozen=True, slots=True)
class ExecStarted:
    step: int


@dataclass(frozen=True, slots=True)
class ExecOutput:
    step: int
    text: str


@dataclass(frozen=True, slots=True)
class ExecFinished:
    step: int
    output: str
    error: str | None
    duration: float
    final: bool


@dataclass(frozen=True, slots=True)
class FileViewed:
    path: str
    start: int
    end: int
    total: int
    scope: Scope = ""


@dataclass(frozen=True, slots=True)
class FileChanged:
    path: str
    kind: ChangeKind
    diff: str
    added: int
    removed: int
    old_path: str | None = None
    scope: Scope = ""


@dataclass(frozen=True, slots=True)
class SearchRan:
    kind: str
    query: str
    count: int
    scope: Scope = ""


@dataclass(frozen=True, slots=True)
class CommandStarted:
    cmd_id: int
    command: str
    cwd: str
    background: bool = False
    scope: Scope = ""


@dataclass(frozen=True, slots=True)
class CommandOutput:
    cmd_id: int
    text: str


@dataclass(frozen=True, slots=True)
class CommandFinished:
    cmd_id: int
    exit_code: int | None
    duration: float
    status: CommandStatus


@dataclass(frozen=True, slots=True)
class JobInfo:
    job_id: int
    command: str
    pid: int
    running: bool
    exit_code: int | None
    started: float
    log_path: str


@dataclass(frozen=True, slots=True)
class JobsChanged:
    jobs: tuple[JobInfo, ...]


@dataclass(frozen=True, slots=True)
class SubQueryProgress:
    """Progress of llm_query / llm_query_batched fan-out from the REPL."""

    query_id: int
    total: int
    done: int
    scope: Scope = ""


@dataclass(frozen=True, slots=True)
class SubAgentStarted:
    agent_id: int
    task: str


@dataclass(frozen=True, slots=True)
class SubAgentProgress:
    agent_id: int
    step: int
    activity: str


@dataclass(frozen=True, slots=True)
class SubAgentFinished:
    agent_id: int
    result: str
    steps: int
    ok: bool


@dataclass(frozen=True, slots=True)
class PlanItem:
    text: str
    status: PlanStatus


@dataclass(frozen=True, slots=True)
class PlanUpdated:
    items: tuple[PlanItem, ...]


@dataclass(frozen=True, slots=True)
class UsageUpdated:
    model: str
    prompt_tokens: int
    completion_tokens: int
    context_window: int | None
    total_cost: float
    cached_tokens: int = 0


@dataclass(frozen=True, slots=True)
class Compacted:
    steps: int
    before_chars: int
    after_chars: int


@dataclass(frozen=True, slots=True)
class TurnFinished:
    turn: int
    response: str
    status: TurnStatus
    error: str | None
    duration: float
    steps: int


@dataclass(frozen=True, slots=True)
class Notice:
    level: Literal["info", "warn", "error"]
    text: str


@dataclass(frozen=True, slots=True)
class ApprovalRequested:
    request_id: int
    title: str
    detail: str


type Event = (
    TurnStarted
    | StepStarted
    | ReasoningDelta
    | CodeDelta
    | ThinkingDelta
    | ResponseDelta
    | StepPlanned
    | ExecStarted
    | ExecOutput
    | ExecFinished
    | FileViewed
    | FileChanged
    | SearchRan
    | CommandStarted
    | CommandOutput
    | CommandFinished
    | JobsChanged
    | SubQueryProgress
    | SubAgentStarted
    | SubAgentProgress
    | SubAgentFinished
    | PlanUpdated
    | UsageUpdated
    | Compacted
    | TurnFinished
    | Notice
    | ApprovalRequested
)

type Emit = Callable[[Event], None]


def drop(_event: Event) -> None:
    """An emitter that ignores everything (useful default for tools used outside an agent)."""
