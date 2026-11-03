"""The frond TUI: layout, input handling, and the bridge to the agent thread.

The app is a state machine fed by two queues: terminal input (keys, mouse, paste, resize) and agent
events. ``draw`` renders the current state into a cell buffer and is pure apart from bookkeeping for
mouse hit-testing, which is what lets ``frond.tui.headless`` drive the very same app without a terminal.
"""

from __future__ import annotations

import logging
import queue
import re
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol

from frond import events as ev
from frond.agent.policy import Decision
from frond.agent.session import TurnRecord
from frond.tui.blocks import (
    Block,
    CommandCard,
    Ctx,
    DiffCard,
    Item,
    NoticeBlock,
    PlanBlock,
    ResponseBlock,
    SearchItem,
    StepBlock,
    SubAgentCard,
    SubQueryItem,
    TurnFooter,
    UserBlock,
    ViewItem,
    WelcomeBlock,
    fmt_duration,
)
from frond.tui.editor import Editor
from frond.tui.keys import Decoder, Focus, InputEvent, Key, Mouse, Paste
from frond.tui.markdown import MarkdownRenderer
from frond.tui.screen import Buffer, Renderer
from frond.tui.style import ColorMode, Style, Theme, blend, luminance, make_theme
from frond.tui.terminal import Terminal
from frond.tui.text import Line, Span, line_width, pad, str_width, styled, truncate
from frond.workspace import Workspace

MAX_INPUT_ROWS = 8
MAX_KEPT_OUTPUT = 200_000
FRAME_INTERVAL = 1 / 60
MAX_MENTION_BYTES = 400_000
COMMANDS: tuple[tuple[str, str], ...] = (
    ("help", "keys and commands"),
    ("new", "start a fresh conversation"),
    ("reset", "restart the Python REPL (forget its variables)"),
    ("undo", "revert the files changed in the last turn"),
    ("details", "show or hide full code, output and diffs (ctrl+o)"),
    ("copy", "copy the last answer to the clipboard"),
    ("jobs", "list background jobs"),
    ("kill", "stop background jobs: /kill [job]"),
    ("model", "show the models in use"),
    ("quit", "exit frond"),
)
HELP = """\
Keys
  enter          send · while the agent works: steer it (it reads your message before its next step)
  tab            while the agent works: queue the message for after the turn instead
  ctrl+j / alt+enter / shift+enter   new line   (or end a line with \\)
  esc            stop the agent · close a popup
  ctrl+c         clear the input · stop the agent · press twice to quit
  ↑ ↓            move in the input · recall history · ↑ on empty input edits the last queued message
  pgup pgdn      scroll the transcript (mouse wheel works too; click a card to expand it)
  ctrl+o         toggle full details for code, output and diffs
  ctrl+l         redraw · ctrl+z suspend
  @              attach files or folders · /  run a command
Text selection: hold shift (option in iTerm2/Terminal.app) while dragging, or use /copy.
Commands: /new /undo /reset /details /copy /jobs /kill /model /quit
/undo reverts the files frond changed in its last turn (changes made by shell commands are not tracked)."""


class AgentLike(Protocol):
    """What the UI needs from the agent (the real Agent, or a stub in tests)."""

    def start_turn(self, request: str, attachments: dict[str, str] | None = None) -> None: ...
    def steer(self, text: str) -> bool: ...
    def cancel(self) -> None: ...
    def undo(self) -> str: ...
    def reset_repl(self) -> None: ...
    def clear(self) -> None: ...
    def close(self) -> None: ...


@dataclass
class ApprovalRequest:
    title: str
    detail: str
    done: threading.Event = field(default_factory=threading.Event)
    decision: Decision = "no"


@dataclass
class Popup:
    kind: Literal["mention", "command"]
    items: list[tuple[str, str]]  # (value, description)
    selected: int = 0
    start: int = 0
    end: int = 0
    query: str = ""


@dataclass
class Hit:
    kind: Literal["button", "block", "popup", "jobs"]
    x0: int
    x1: int
    y0: int
    y1: int
    block: Block | None = None
    first_row: int = 0
    index: int = 0


class App:
    def __init__(
        self,
        workspace: Workspace,
        *,
        model: str,
        sub_model: str,
        theme: Theme | None = None,
        color_mode: ColorMode = "truecolor",
        note: str | None = None,
    ) -> None:
        self.workspace = workspace
        self.model = model
        self.sub_model = sub_model
        self.theme = theme or make_theme(dark=True)
        self.color_mode = color_mode
        self.md = MarkdownRenderer(self.theme, self._link_for)
        self.agent: AgentLike | None = None
        self.inbox: queue.SimpleQueue[ev.Event | ApprovalRequest] = queue.SimpleQueue()
        self.terminal: Terminal | None = None
        self.editor = Editor()
        self.decoder = Decoder()
        branch = None
        if workspace.git_root:
            head = workspace.git_root / ".git" / "HEAD"
            try:
                ref = head.read_text().strip()
                branch = ref.rsplit("/", 1)[-1] if ref.startswith("ref:") else ref[:8]
            except OSError:
                branch = None
        self.branch = branch
        self.blocks: list[Block] = [WelcomeBlock(model, sub_model, _display_path(workspace.root), branch, note)]
        self.queue: list[str] = []
        self.running = False
        self.stopping = False
        self.turn_started = 0.0
        self.steps: dict[int, StepBlock] = {}
        self.current: StepBlock | None = None
        self.response: ResponseBlock | None = None
        self.plan: PlanBlock | None = None
        self.undo_block: StepBlock | None = None
        self.commands: dict[int, CommandCard] = {}
        self.subagents: dict[int, SubAgentCard] = {}
        self.subqueries: dict[int, SubQueryItem] = {}
        self.usage: ev.UsageUpdated | None = None
        self.jobs: tuple[ev.JobInfo, ...] = ()
        self.last_response = ""
        self.cost_at_turn_start = 0.0
        self.scroll = 0
        self.details = False
        self.popup: Popup | None = None
        self.approval: ApprovalRequest | None = None
        self.pending_approvals: list[ApprovalRequest] = []
        self.quit_armed = 0.0
        self.flash_text = ""
        self.flash_until = 0.0
        self.focused = True
        self.should_quit = False
        self.tick = 0
        self.dirty = True
        self.hits: list[Hit] = []
        self._transcript_height = 10
        self._input_width = 40

    # ── wiring ───────────────────────────────────────────────────────────────

    def attach(self, agent: AgentLike) -> None:
        self.agent = agent

    def emit(self, event: ev.Event) -> None:
        """Called from the agent thread."""
        self.inbox.put(event)
        if self.terminal is not None:
            self.terminal.wake()

    def approver(self, title: str, detail: str) -> Decision:
        """Called from the agent thread; blocks until the user answers in the UI."""
        request = ApprovalRequest(title, detail)
        self.inbox.put(request)
        if self.terminal is not None:
            self.terminal.wake()
        while not request.done.wait(0.1):
            if self.should_quit:
                return "no"
        return request.decision

    def _link_for(self, ref: str) -> str | None:
        path = ref.split(":", 1)[0]
        p = self.workspace.resolve(path)
        return p.as_uri() if p.exists() else None

    def flash(self, text: str, seconds: float = 2.5) -> None:
        self.flash_text, self.flash_until = text, time.monotonic() + seconds
        self.dirty = True

    def add(self, block: Block) -> None:
        self.blocks.append(block)
        self.dirty = True

    # ── agent events ─────────────────────────────────────────────────────────

    def pump(self, limit: int = 5000) -> int:
        n = 0
        while n < limit:
            try:
                item = self.inbox.get_nowait()
            except queue.Empty:
                break
            n += 1
            if isinstance(item, ApprovalRequest):
                if self.approval is None:
                    self.approval = item
                    self.popup = None
                    if self.terminal is not None:
                        self.terminal.bell()
                else:
                    self.pending_approvals.append(item)  # parallel tool calls can ask at once: one at a time
            else:
                self.apply(item)
            self.dirty = True
        return n

    def _step(self, step: int) -> StepBlock:
        block = self.steps.get(step)
        if block is None:
            block = StepBlock(step, 0)
            self.steps[step] = block
            self.add(block)
        return block

    def _attach_item(self, item: Item, scope: str = "") -> None:
        if scope == "undo" and self.undo_block is not None:
            self.undo_block.items.append(item)
            self.undo_block.touch()
            return
        if scope:
            return  # sub-agent activity is summarised on its card
        target = self.current
        if target is None:
            target = self._step(max(self.steps, default=0) or 1)
        target.items.append(item)
        target.touch()

    def apply(self, e: ev.Event) -> None:
        match e:
            case ev.TurnStarted():
                self.flash_until = 0.0
                self.steps.clear()
                self.commands.clear()
                self.subqueries.clear()
                self.current = self.response = self.plan = None
            case ev.StepStarted(step=step, max_steps=max_steps):
                block = self._step(step)
                block.max_steps = max_steps
                block.started = time.monotonic()
                self.current = block
            case ev.ReasoningDelta(step=step, text=text):
                block = self._step(step)
                block.reasoning += text
                block.touch()
            case ev.ThinkingDelta(step=step, text=text):
                block = self._step(step or max(self.steps, default=1))
                block.thinking += text
                block.touch()
            case ev.CodeDelta(step=step, text=text):
                block = self._step(step)
                block.code += text
                block.state = "writing"
                block.touch()
            case ev.StepPlanned(step=step, reasoning=reasoning, code=code):
                block = self._step(step)
                block.reasoning, block.code = reasoning, code
                block.touch()
            case ev.ExecStarted(step=step):
                block = self._step(step)
                block.state = "running"
                block.started = time.monotonic()
                block.touch()
            case ev.ExecOutput(step=step, text=text):
                block = self._step(step)
                block.output += text
                if len(block.output) > MAX_KEPT_OUTPUT:
                    block.output = block.output[-MAX_KEPT_OUTPUT // 2 :]
                block.touch()
            case ev.ExecFinished(step=step, output=output, error=error, duration=duration, final=final):
                block = self._step(step)
                block.duration = duration
                if final:
                    block.state = "final"
                elif error:
                    block.state, block.error = "error", error.removeprefix("[Error] ")
                    if self.response is not None and self.response.streaming:
                        self.blocks.remove(self.response)  # the SUBMIT failed: retract the streamed answer
                        self.response = None
                else:
                    block.state = "done"
                    kept = (
                        output
                        if len(output) <= MAX_KEPT_OUTPUT
                        else output[: MAX_KEPT_OUTPUT // 2]
                        + (
                            f"\n… [{len(output) - MAX_KEPT_OUTPUT:,} characters not shown] …\n"
                            + output[-MAX_KEPT_OUTPUT // 2 :]
                        )
                    )
                    block.output = "" if output.startswith("(no output") else kept
                block.touch()
            case ev.ResponseDelta(text=text):
                if self.response is None:
                    self.response = ResponseBlock()
                    self.add(self.response)
                self.response.text += text
                self.response.touch()
            case ev.FileViewed(path=path, start=start, end=end, total=total, scope=scope):
                self._attach_item(ViewItem(path, start, end, total), scope)
            case ev.SearchRan(kind=kind, query=query, count=count, scope=scope):
                self._attach_item(SearchItem(kind, query, count), scope)
            case ev.FileChanged(path=path, kind=kind, diff=diff, added=added, removed=removed, old_path=old, scope=sc):
                self._attach_item(DiffCard(path, kind, diff, added, removed, old), sc)
            case ev.CommandStarted(cmd_id=cid, command=command, background=background, scope=scope):
                card = CommandCard(cid, command, background)
                self.commands[cid] = card
                self._attach_item(card, scope)
            case ev.CommandOutput(cmd_id=cid, text=text):
                card = self.commands.get(cid)
                if card is not None:
                    card.output += text
                    if len(card.output) > 400_000:
                        card.output = card.output[-300_000:]
                    self._touch_owner(card)
            case ev.CommandFinished(cmd_id=cid, exit_code=code, duration=duration, status=status):
                card = self.commands.get(cid)
                if card is not None:
                    card.status, card.exit_code, card.duration = status, code, duration
                    self._touch_owner(card)
            case ev.JobsChanged(jobs=jobs):
                self.jobs = jobs
            case ev.SubQueryProgress(query_id=qid, total=total, done=done, scope=scope):
                item = self.subqueries.get(qid)
                if item is None:
                    item = SubQueryItem(total)
                    self.subqueries[qid] = item
                    self._attach_item(item, scope)
                item.done = done
                self._touch_owner(item)
            case ev.SubAgentStarted(agent_id=aid, task=task):
                card = SubAgentCard(aid, task)
                self.subagents[aid] = card
                self._attach_item(card)
            case ev.SubAgentProgress(agent_id=aid, step=step, activity=activity):
                card = self.subagents.get(aid)
                if card is not None:
                    card.step, card.activity = step, activity
                    self._touch_owner(card)
            case ev.SubAgentFinished(agent_id=aid, result=result, steps=steps, ok=ok):
                card = self.subagents.get(aid)
                if card is not None:
                    card.result, card.ok, card.step = result, ok, steps
                    card.duration = time.monotonic() - card.started
                    self._touch_owner(card)
            case ev.PlanUpdated(items=items):
                if self.plan is not None and self.plan in self.blocks:
                    self.blocks.remove(self.plan)
                self.plan = PlanBlock(items)
                self.add(self.plan)
            case ev.UsageUpdated():
                self.usage = e
            case ev.Compacted(steps=steps, before_chars=before, after_chars=after):
                self.add(
                    NoticeBlock(
                        "info",
                        f"folded {steps} earlier steps of this turn into an index "
                        f"({before // 1000}k → {after // 1000}k chars); the step log keeps them whole",
                    )
                )
            case ev.Notice(level=level, text=text):
                self.add(NoticeBlock(level, text))
            case ev.SteerDelivered(text=text, step=step):
                block = next(
                    (b for b in self.blocks if isinstance(b, UserBlock) and b.steer == "sent" and b.text == text), None
                )
                if block is not None:
                    block.steer, block.step = "read", step
                    block.touch()
            case ev.SteersReturned(texts=texts):
                for text in texts:  # the turn ended first: they run next, in order, ahead of what was queued
                    block = next(
                        (b for b in self.blocks if isinstance(b, UserBlock) and b.steer == "sent" and b.text == text),
                        None,
                    )
                    if block is not None:
                        self.blocks.remove(block)
                self.queue[:0] = list(texts)
            case ev.TurnFinished(response=response, status=status, error=error, duration=duration, steps=steps):
                self._finish_turn(response, status, error, duration, steps)
            case _:
                pass

    def _touch_owner(self, item: Item) -> None:
        for block in reversed(self.blocks):
            if isinstance(block, StepBlock) and item in block.items:
                block.touch()
                return

    def _finish_turn(
        self, response: str, status: ev.TurnStatus, error: str | None, duration: float, steps: int
    ) -> None:
        self.flash_until = 0.0
        self.decline_pending_approvals()
        for block in self.steps.values():
            if block.state in ("thinking", "writing", "running"):
                block.state = "stopped" if status == "cancelled" else "done"
                block.touch()
        for card in self.commands.values():
            if card.status is None:
                card.status = "cancelled"
        if response:
            if self.response is None:
                self.response = ResponseBlock()
                self.add(self.response)
            self.response.text = response
            self.response.streaming = False
            self.response.touch()
            self.last_response = response
        elif self.response is not None:
            self.blocks.remove(self.response)
        cost = None
        if self.usage is not None and self.usage.total_cost:
            cost = self.usage.total_cost - self.cost_at_turn_start
        self.add(TurnFooter(status, steps, duration, error, cost))
        self.response = None
        self.current = None
        self.running = self.stopping = False
        if duration > 10 and not self.focused and self.terminal is not None:
            self.terminal.bell()
        if self.queue and status != "error":
            self.start_turn(self.queue.pop(0))
        elif self.queue:
            self.flash(f"{len(self.queue)} queued message(s) held after the error · enter sends the next")

    # ── turns ────────────────────────────────────────────────────────────────

    def mentions(self, text: str) -> dict[str, str]:
        found: dict[str, str] = {}
        budget = MAX_MENTION_BYTES
        for raw in re.findall(r"(?<!\S)@(\S+)", text):
            ref = raw.rstrip(".,;:!?)'\"")
            path = self.workspace.resolve(ref)
            rel = self.workspace.rel(path)
            if rel in found or not path.exists():
                continue
            if path.is_dir():
                try:
                    entries = sorted(p.name + ("/" if p.is_dir() else "") for p in path.iterdir())
                except OSError:
                    continue
                found[rel] = f"(directory with {len(entries)} entries)\n" + "\n".join(entries[:300])
                continue
            try:
                with path.open("rb") as f:  # never more than the cap, however large the file is
                    data = f.read(min(budget, 200_000) + 1)
            except OSError:
                continue
            if b"\0" in data[:8192]:
                found[rel] = f"(binary file, {path.stat().st_size:,} bytes)"
                continue
            content = data.decode("utf-8", errors="replace")
            if len(data) > 200_000:
                content = content[:200_000] + f"\n… (truncated; file is {path.stat().st_size:,} bytes)"
            budget -= len(content)
            found[rel] = content
            if budget <= 0:
                break
        return found

    def restore(self, records: list[TurnRecord], source: str) -> None:
        """Show the turns of a resumed conversation (their replies; the step-by-step detail is not kept)."""
        for record in records:
            if record.request == "/undo":
                self.add(NoticeBlock("info", record.response.strip("()")))
                continue
            self.add(UserBlock(record.request))
            if record.response:
                block = ResponseBlock()
                block.text, block.streaming = record.response, False
                self.add(block)
                self.last_response = record.response
            self.add(TurnFooter(record.status, record.steps, record.duration, record.error, None))
        self.add(
            NoticeBlock(
                "info",
                f"resumed {len(records)} earlier turn{'s' if len(records) != 1 else ''} "
                f"from {source}; the Python REPL starts fresh",
            )
        )

    def start_turn(self, text: str) -> None:
        if self.agent is None:
            self.flash("no agent attached")
            return
        attachments = self.mentions(text)
        self.add(UserBlock(text, tuple(attachments)))
        self.running, self.stopping = True, False
        self.turn_started = time.monotonic()
        self.cost_at_turn_start = self.usage.total_cost if self.usage else 0.0
        self.scroll = 0
        try:
            self.agent.start_turn(text, attachments)
        except RuntimeError as exc:
            self.running = False
            self.add(NoticeBlock("error", str(exc)))

    def stop(self) -> None:
        if self.running and not self.stopping and self.agent is not None:
            self.stopping = True
            self.decline_pending_approvals()
            self.agent.cancel()
            self.flash("stopping…")

    def decline_pending_approvals(self) -> None:
        for request in [r for r in (self.approval, *self.pending_approvals) if r is not None]:
            request.decision = "no"
            request.done.set()
        self.approval = None
        self.pending_approvals.clear()

    def submit(self, *, queue: bool = False) -> None:
        text = self.editor.text
        if text.endswith("\\") and self.editor.cursor == len(text):
            self.editor.backspace()
            self.editor.insert("\n")
            return
        text = text.strip()
        if not text:
            return
        self.popup = None
        if text.startswith("/") and "\n" not in text:
            self.editor.remember(text)
            self.editor.clear()
            self.command(text[1:])
            return
        self.editor.remember(text)
        self.editor.clear()
        if self.running:
            if not queue and self.agent is not None and not self.stopping and self.agent.steer(text):
                self.add(UserBlock(text, steer="sent"))
                self.flash("sent · frond reads it before its next step (tab queues instead)")
                return
            self.queue.append(text)
            self.flash("queued · runs after the current turn")
            return
        self.start_turn(text)

    def command(self, line: str) -> None:
        name, _, arg = line.strip().partition(" ")
        name = name.lower()
        match name:
            case "help" | "?":
                self.add(NoticeBlock("info", HELP))
            case "new" | "clear":
                if self.running:
                    self.flash("stop the current turn first (esc)")
                    return
                if self.agent is not None:
                    self.agent.clear()
                self.blocks = self.blocks[:1]
                self.queue.clear()
                self.flash("new conversation")
            case "reset":
                if self.running:
                    self.flash("stop the current turn first (esc)")
                    return
                if self.agent is not None:
                    self.agent.reset_repl()
                self.add(NoticeBlock("info", "restarted the Python REPL; its variables are gone"))
            case "undo":
                if self.running:
                    self.flash("stop the current turn first (esc)")
                    return
                if self.agent is not None:
                    self.undo_block = StepBlock(0, 0)
                    self.undo_block.state = "done"
                    self.add(self.undo_block)
                    summary = self.agent.undo()
                    self.undo_block.reasoning = "↶ " + summary[0].upper() + summary[1:]
                    self.undo_block.touch()
            case "details":
                self.toggle_details()
            case "copy":
                if not self.last_response:
                    self.flash("nothing to copy yet")
                elif self.terminal is not None:
                    self.terminal.copy_to_clipboard(self.last_response)
                    self.flash("copied the last answer")
            case "jobs":
                if not self.jobs:
                    self.add(NoticeBlock("info", "no background jobs"))
                else:
                    lines = [
                        f"job {j.job_id}  {'running' if j.running else f'exited {j.exit_code}'}  {j.command}"
                        for j in self.jobs
                    ]
                    self.add(NoticeBlock("info", "\n".join(lines)))
            case "kill":
                killer = getattr(self.agent, "jobs", None)
                targets = [j.job_id for j in self.jobs if j.running and (not arg or str(j.job_id) == arg.strip())]
                for job_id in targets:
                    if killer is not None:
                        killer.kill(job_id)
                self.flash(f"stopped {len(targets)} job(s)" if targets else "no matching running job")
            case "model" | "models":
                window = self.usage.context_window if self.usage else None
                text = f"model {self.model} · sub-queries {self.sub_model}"
                if window:
                    text += f" · context window {window:,} tokens"
                self.add(NoticeBlock("info", text))
            case "quit" | "exit" | "q":
                self.should_quit = True
            case _:
                self.flash(f"unknown command /{name} · try /help")

    def toggle_details(self) -> None:
        self.details = not self.details
        self.flash("details on" if self.details else "details off")

    # ── input ────────────────────────────────────────────────────────────────

    def on_input(self, event: InputEvent) -> None:
        self.dirty = True
        match event:
            case Paste(text=text):
                if self.approval is None:
                    self.editor.insert(text.replace("\t", "    "))
                    self._update_popup()
            case Mouse():
                self.on_mouse(event)
            case Focus(gained=gained):
                self.focused = gained
            case Key():
                self.on_key(event)

    def on_key(self, key: Key) -> None:
        if self.approval is not None:
            self._approval_key(key)
            return
        name = key.name
        if self.popup is not None and self._popup_key(key):
            return
        if key.ctrl and name == "c":
            if self.editor.text:
                self.editor.clear()
                self.popup = None
            elif self.running:
                self.stop()
            elif time.monotonic() - self.quit_armed < 2:
                self.should_quit = True
            else:
                self.quit_armed = time.monotonic()
                self.flash("press ctrl+c again to quit", 2)
            return
        if key.ctrl and name == "d" and not self.editor.text:
            self.should_quit = True
            return
        if name == "escape":
            if self.popup is not None:
                self.popup = None
            elif self.running:
                self.stop()
            elif self.scroll:
                self.scroll = 0
            return
        if name == "enter" and not (key.alt or key.shift or key.ctrl):
            self.submit()
            self._update_popup()
            return
        if (name == "enter" and (key.alt or key.shift)) or (key.ctrl and name == "j"):
            self.editor.insert("\n")
            return
        width = self._input_width
        if name == "up" and not key.ctrl and not key.alt:
            if key.shift:
                self.scroll_by(3)
            elif not self.editor.text and self.queue:
                self.editor.set(self.queue.pop())
                self.flash("editing the last queued message")
            elif not self.editor.move_vertical(-1, width):
                self.editor.history_prev()
            self._update_popup()
            return
        if name == "down" and not key.ctrl and not key.alt:
            if key.shift:
                self.scroll_by(-3)
            elif not self.editor.move_vertical(1, width):
                self.editor.history_next()
            self._update_popup()
            return
        if name == "pageup":
            self.scroll_by(max(1, self._transcript_height - 2))
            return
        if name == "pagedown":
            self.scroll_by(-max(1, self._transcript_height - 2))
            return
        if key.ctrl and name in ("home", "end"):
            self.scroll = 10**9 if name == "home" else 0
            return
        if key.ctrl and name == "o":
            self.toggle_details()
            return
        if key.ctrl and name == "l":
            if self.terminal is not None:
                self._renderer_invalidate()
            return
        if key.ctrl and name == "z":
            if self.terminal is not None:
                self.terminal.suspend()
                self._renderer_invalidate()
            return
        self._edit_key(key)
        self._update_popup()

    def _edit_key(self, key: Key) -> None:
        e = self.editor
        name = key.name
        if key.ctrl:
            actions: dict[str, Callable[[], None]] = {
                "a": e.home,
                "e": e.end,
                "k": e.kill_to_end,
                "u": e.kill_to_start,
                "w": e.kill_word_left,
                "y": e.yank,
                "_": e.undo,
                "b": e.left,
                "f": e.right,
                "h": e.backspace,
                "left": e.word_left,
                "right": e.word_right,
                "backspace": e.kill_word_left,
                "delete": e.kill_word_right,
            }
            if name in actions:
                actions[name]()
            return
        if key.alt:
            alt_actions: dict[str, Callable[[], None]] = {
                "b": e.word_left,
                "f": e.word_right,
                "d": e.kill_word_right,
                "backspace": e.kill_word_left,
                "left": e.word_left,
                "right": e.word_right,
            }
            if name in alt_actions:
                alt_actions[name]()
            return
        simple: dict[str, Callable[[], None]] = {
            "backspace": e.backspace,
            "delete": e.delete,
            "left": e.left,
            "right": e.right,
            "home": e.home,
            "end": e.end,
        }
        if name in simple:
            simple[name]()
        elif name == "tab":
            if self.running and self.editor.text.strip():
                self.submit(queue=True)
        elif name == "space":
            e.insert(" ")
        elif key.char is not None:
            e.insert(key.char)

    def _approval_key(self, key: Key) -> None:
        request = self.approval
        if request is None:
            return
        choices: dict[str, Decision] = {"y": "yes", "a": "always", "n": "no", "escape": "no"}
        choice = choices.get(key.name)
        if key.ctrl and key.name == "c":
            choice = "no"
        if choice is None:
            return
        request.decision = choice
        request.done.set()
        self.approval = self.pending_approvals.pop(0) if self.pending_approvals else None
        self.flash({"yes": "allowed once", "always": "allowed for this session", "no": "declined"}[choice])

    # ── popup ────────────────────────────────────────────────────────────────

    def _update_popup(self) -> None:
        token = self.editor.token()
        if token is None:
            self.popup = None
            return
        if token.kind == "command":
            items = [(f"/{n}", d) for n, d in COMMANDS if n.startswith(token.query.lower())]
        else:
            items = [(p, "") for p in self.workspace.mention_index().rank(token.query, limit=40)]
        if not items:
            self.popup = None
            return
        previous = self.popup
        selected = 0
        if previous is not None and previous.kind == token.kind and previous.items and previous.query == token.query:
            selected = min(previous.selected, len(items) - 1)
        self.popup = Popup(token.kind, items, selected, token.start, token.end, token.query)

    def _popup_key(self, key: Key) -> bool:
        popup = self.popup
        assert popup is not None
        if key.name in ("up", "down") and not key.alt:
            step = -1 if key.name == "up" else 1
            popup.selected = (popup.selected + step) % len(popup.items)
            return True
        if key.ctrl and key.name in ("p", "n"):
            popup.selected = (popup.selected + (-1 if key.name == "p" else 1)) % len(popup.items)
            return True
        if key.name in ("tab", "enter") and not (key.alt or key.shift):
            self._accept_popup()
            return True
        return False

    def _accept_popup(self, index: int | None = None) -> None:
        popup = self.popup
        if popup is None:
            return
        value = popup.items[popup.selected if index is None else index][0]
        if popup.kind == "command":
            self.popup = None
            self.editor.clear()
            self.command(value[1:])
            return
        quoted = value if " " not in value else value.replace(" ", "\\ ")
        self.editor.replace(popup.start, popup.end, f"@{quoted} ")
        self.popup = None
        self._update_popup()

    # ── mouse and scrolling ──────────────────────────────────────────────────

    def scroll_by(self, lines: int) -> None:
        self.scroll = max(0, self.scroll + lines)
        self.dirty = True

    def on_mouse(self, m: Mouse) -> None:
        if m.kind == "wheel_up":
            self.scroll_by(3)
            return
        if m.kind == "wheel_down":
            self.scroll_by(-3)
            return
        if m.kind != "press" or m.button != 0:
            return
        for hit in reversed(self.hits):
            if hit.x0 <= m.x < hit.x1 and hit.y0 <= m.y < hit.y1:
                if hit.kind == "button":
                    if self.running and not self.editor.text.strip():
                        self.stop()
                    else:
                        self.submit()
                elif hit.kind == "popup":
                    self._accept_popup(hit.index)
                elif hit.kind == "jobs":
                    self.command("jobs")
                elif hit.kind == "block" and hit.block is not None:
                    row = hit.first_row + (m.y - hit.y0)
                    if isinstance(hit.block, StepBlock):
                        hit.block.click(row)
                    elif isinstance(hit.block, NoticeBlock | ResponseBlock):
                        pass
                    else:
                        hit.block.toggle()
                return

    def _renderer_invalidate(self) -> None:
        renderer = getattr(self, "renderer", None)
        if isinstance(renderer, Renderer):
            renderer.invalidate()

    # ── drawing ──────────────────────────────────────────────────────────────

    def ctx(self) -> Ctx:
        return Ctx(self.theme, self.md, self.details, self.tick, time.monotonic())

    def draw(self, width: int, height: int) -> Buffer:
        buf = Buffer(width, height)
        self.hits = []
        ctx = self.ctx()
        status_y = height - 1
        input_rows, input_lines, caret = self._input_layout(width)
        input_h = input_rows + 2
        queue_lines = self._queue_lines(width)
        approval_lines = self._approval_lines(width) if self.approval else []
        bottom = status_y - input_h - len(queue_lines) - len(approval_lines)
        transcript_h = max(1, bottom)
        self._transcript_height = transcript_h
        self._draw_transcript(buf, 0, transcript_h, width, ctx)
        y = transcript_h
        for line in approval_lines:
            buf.put_line(0, y, line)
            y += 1
        for line in queue_lines:
            buf.put_line(0, y, line)
            y += 1
        self._draw_input(buf, y, width, input_rows, input_lines, caret)
        if self.popup is not None and self.approval is None:
            self._draw_popup(buf, y, width)
        self._draw_status(buf, status_y, width)
        self.dirty = False
        return buf

    def _draw_transcript(self, buf: Buffer, top: int, height: int, width: int, ctx: Ctx) -> None:
        margin = 2
        inner = max(10, width - margin * 2)
        rendered = [block.lines(inner, ctx) for block in self.blocks]
        gaps = [0 if i == 0 or isinstance(block, TurnFooter) else 1 for i, block in enumerate(self.blocks)]
        total = sum(map(len, rendered)) + sum(gaps)
        self.scroll = min(self.scroll, max(0, total - height))
        end = total - self.scroll
        start = max(0, end - height)
        y = top + height - (end - start)
        pos = 0
        for block, lines, gap in zip(self.blocks, rendered, gaps, strict=True):
            first = pos + gap
            pos = first + len(lines)
            if pos <= start or first >= end:
                continue
            lo, hi = max(start, first), min(end, pos)
            row_y = y + (lo - start)
            if lo - first < len(lines):
                self.hits.append(Hit("block", margin, margin + inner, row_y, row_y + (hi - lo), block, lo - first))
            for n in range(lo - first, hi - first):
                buf.put_line(margin, row_y, lines[n], max_x=margin + inner)
                row_y += 1
        if self.scroll:
            label = f" ↓ {self.scroll} more line{'s' if self.scroll != 1 else ''} · esc to jump down "
            x = max(0, width - str_width(label) - 2)
            buf.put(x, top + height - 1, label, self.theme.info + Style(bg=self.theme.panel_alt))

    def _input_layout(self, width: int) -> tuple[int, list[tuple[str, int]], tuple[int, int]]:
        button_w = 11
        text_w = max(8, width - 4 - 2 - button_w)  # borders, prompt glyph, button column
        self._input_width = text_w
        rows = self.editor.layout(text_w) if self.editor.text else []
        caret_col, caret_row = self.editor.caret(text_w) if self.editor.text else (0, 0)
        lines = [(r.text, r.start) for r in rows] or [("", 0)]
        while caret_row >= len(lines):
            lines.append(("", len(self.editor.text)))
        first = max(0, caret_row - MAX_INPUT_ROWS + 1)
        visible = lines[first : first + MAX_INPUT_ROWS]
        return len(visible), visible, (caret_col, caret_row - first)

    def _draw_input(
        self, buf: Buffer, y: int, width: int, rows: int, lines: list[tuple[str, int]], caret: tuple[int, int]
    ) -> None:
        t = self.theme
        busy = self.running
        has_text = bool(self.editor.text.strip())
        border = t.border_focus if has_text else t.border
        buf.put(0, y, "╭" + "─" * (width - 2) + "╮", border)
        for i in range(rows):
            buf.put(0, y + 1 + i, "│", border)
            buf.put(width - 1, y + 1 + i, "│", border)
        buf.put(0, y + rows + 1, "╰" + "─" * (width - 2) + "╯", border)
        prompt_style = t.accent_bold if not busy else t.faint
        buf.put(2, y + 1, "›", prompt_style)
        text_x = 4
        if not self.editor.text:
            room = width - 13 - text_x
            options = (
                ["type to steer the running turn · tab queues · esc stops", "type to steer · esc stops"]
                if busy
                else [
                    "Ask frond to build, fix or explain something…  @ attach · / commands",
                    "Ask frond to build, fix or explain something…",
                    "Ask frond anything…",
                ]
            )
            hint = next((o for o in options if str_width(o) <= room), "")
            buf.put(text_x, y + 1, hint, t.faint, max_x=width - 13)
        else:
            highlights = [(m.start(), m.end()) for m in re.finditer(r"(?<!\S)@\S+", self.editor.text)]
            if self.editor.text.startswith("/"):
                end = self.editor.text.find(" ")
                highlights.append((0, len(self.editor.text) if end == -1 else end))
            for i, (text, start) in enumerate(lines):
                x = text_x
                for j, ch in enumerate(text):
                    pos = start + j
                    style = t.accent if any(a <= pos < b for a, b in highlights) else Style()
                    x = buf.put(x, y + 1 + i, ch, style)
        # The send/stop button lives at the bottom-right inside the box.
        if busy and self.stopping:
            label, style = " ◌ stopping ", t.faint + Style(bg=t.panel_alt)
        elif busy and not has_text:
            label, style = (
                " ■ stop ",
                Style(fg=t.error.fg, bg=blend(t.panel_alt, t.error.fg or (200, 80, 80), 0.18), bold=True),
            )
        elif busy:
            label, style = " ⏎ steer ", Style(fg=t.info.fg, bg=t.panel_alt, bold=True)
        else:
            label, style = (
                " ⏎ send ",
                (Style(fg=t.accent.fg, bg=t.panel_alt, bold=True) if has_text else t.faint + Style(bg=t.panel_alt)),
            )
        bx = width - 2 - str_width(label)
        by = y + rows
        buf.put(bx, by, label, style)
        self.hits.append(Hit("button", bx, bx + str_width(label), by, by + 1))
        if self.approval is None:
            col, row = caret
            buf.cursor = (min(width - 3, text_x + col), y + 1 + row)

    def _queue_lines(self, width: int) -> list[Line]:
        t = self.theme
        if not self.queue:
            return []
        out: list[Line] = []
        for i, text in enumerate(self.queue[:3]):
            label = Span(" ↳ queued " if i == 0 else "          ", t.info)
            body = truncate(styled(text.replace("\n", " ⏎ "), t.muted), width - 14)
            out.append([Span(" "), label, Span(" "), *body])
        if len(self.queue) > 3:
            out.append([Span(" " * 12), Span(f"… {len(self.queue) - 3} more", t.faint)])
        out[-1] = [*out[-1]]
        hint = "↑ edit last"
        if line_width(out[0]) + str_width(hint) + 4 < width:
            out[0] = [*pad(out[0], width - str_width(hint) - 2), Span(hint, t.faint)]
        return out

    def _approval_lines(self, width: int) -> list[Line]:
        t = self.theme
        request = self.approval
        if request is None:
            return []
        bg = Style(bg=blend(t.panel_alt, t.warn.fg or (220, 180, 100), 0.12))
        inner = width - 4

        def row(content: Line) -> Line:
            return [
                Span(" ", bg),
                *pad(truncate([Span(s.text, bg + s.style) for s in content], inner + 2), inner + 2, bg),
                Span(" ", bg),
            ]

        detail = request.detail.replace("\n", " ⏎ ")
        return [
            row([Span("⚠ ", t.warn), Span("approval needed · ", t.warn), Span(request.title, Style(bold=True))]),
            row([Span("  "), *styled(detail, Style(fg=t.text.fg))]),
            row(
                [
                    Span("  "),
                    Span("y", t.accent_bold),
                    Span(" allow once   ", t.muted),
                    Span("a", t.accent_bold),
                    Span(" always this session   ", t.muted),
                    Span("n", t.error),
                    Span(" deny", t.muted),
                ]
            ),
        ]

    def _draw_popup(self, buf: Buffer, input_y: int, width: int) -> None:
        popup = self.popup
        assert popup is not None
        t = self.theme
        visible = 8
        first = max(0, min(popup.selected - visible // 2, len(popup.items) - visible))
        items = popup.items[first : first + visible]
        name_w = max(str_width(v) for v, _ in popup.items)
        w = min(width - 4, max(36, max(name_w + str_width(d) + 7 for _, d in items)))
        h = len(items)
        x0 = 2
        y0 = input_y - h
        bg = Style(bg=t.panel_alt)
        buf.fill(0, y0 - 1, width, h + 1)  # the popup owns these rows: no transcript text bleeding past its edge
        for i, (value, desc) in enumerate(items):
            index = first + i
            y = y0 + i
            selected = index == popup.selected
            row_style = Style(bg=blend(t.panel_alt, t.accent.fg or (120, 200, 140), 0.16)) if selected else bg
            buf.fill(x0, y, w, 1, row_style)
            marker = "› " if selected else "  "
            x = buf.put(x0 + 1, y, marker, row_style + t.accent)
            if popup.kind == "mention":
                head, _, tail = value.rpartition("/")
                if value.endswith("/"):
                    head, _, tail = value[:-1].rpartition("/")
                    tail += "/"
                if head:
                    x = buf.put(x, y, head + "/", row_style + t.muted, max_x=x0 + w - 1)
                buf.put(x, y, tail, row_style + Style(bold=selected), max_x=x0 + w - 1)
            else:
                name_w = max(str_width(v) for v, _ in popup.items)
                buf.put(x, y, value, row_style + t.accent + Style(bold=True), max_x=x0 + w - 1)
                buf.put(x + name_w + 2, y, desc, row_style + t.muted, max_x=x0 + w - 1)
            self.hits.append(Hit("popup", x0, x0 + w, y, y + 1, index=index))
        if len(popup.items) > visible:
            more = f" {popup.selected + 1}/{len(popup.items)} "
            buf.put(x0 + w - str_width(more) - 1, y0, more, bg + t.faint)

    def _draw_status(self, buf: Buffer, y: int, width: int) -> None:
        t = self.theme
        now = time.monotonic()
        left: Line
        if self.flash_text and now < self.flash_until:
            left = [Span(" " + self.flash_text, t.info)]
        elif self.running:
            spin = "◌" if self.stopping else "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"[self.tick % 10]
            left = [
                Span(" " + spin + " ", t.accent),
                *styled(self._activity(), t.muted),
                Span(f" · {fmt_duration(now - self.turn_started)}", t.faint),
            ]
        else:
            where = _display_path(self.workspace.root)
            left = [Span(" ◆ ", t.accent), Span(where, t.faint)]
            if self.branch:
                left.append(Span(f"  ⎇ {self.branch}", t.faint))
        right: Line = []
        running_jobs = [j for j in self.jobs if j.running]
        if running_jobs:
            label = f"⧗ {len(running_jobs)} job{'s' if len(running_jobs) != 1 else ''}"
            right += [Span(label, t.info), Span("   ")]
        if self.queue:
            right += [Span(f"↳ {len(self.queue)} queued", t.info), Span("   ")]
        if self.details:
            right += [Span("details", t.faint), Span("   ")]
        right += self._meter()
        right.append(Span(" "))
        x = buf.put_line(0, y, truncate(left, max(10, width - line_width(right) - 1)))
        rx = width - line_width(right)
        if rx > x:
            buf.put_line(rx, y, right)
            if running_jobs:
                self.hits.append(Hit("jobs", rx, rx + 8, y, y + 1))

    def _activity(self) -> str:
        if self.stopping:
            return "stopping"
        if self.approval:
            return "waiting for your approval"
        block = self.current
        if block is None:
            return "starting"
        prefix = f"step {block.step}" + (f"/{block.max_steps}" if block.max_steps else "")
        running_cmd = next((c for c in self.commands.values() if c.status is None), None)
        if running_cmd is not None:
            cmd = running_cmd.command.split("\n")[0]
            return f"{prefix} · $ {cmd[:40]}{'…' if len(cmd) > 40 else ''}"
        running_sub = next((s for s in self.subagents.values() if s.result is None), None)
        if running_sub is not None:
            return f"{prefix} · subagent: {running_sub.activity[:40]}"
        if self.response is not None and self.response.streaming:
            return "writing the answer"
        return {
            "thinking": f"{prefix} · thinking",
            "writing": f"{prefix} · writing code",
            "running": f"{prefix} · running",
        }.get(block.state, prefix)

    def _meter(self) -> Line:
        """The context meter: a thin bar that fills as the prompt approaches the model's context window."""
        t = self.theme
        usage = self.usage
        cells = 12
        if usage is None or not usage.context_window:
            used, window = (usage.prompt_tokens if usage else 0), (usage.context_window if usage else None)
            label = f" {_tokens(used)}" if used else " ctx"
            return [Span("─" * cells, Style(fg=t.meter_track)), Span(label, t.faint)]
        used, window = usage.prompt_tokens, usage.context_window
        frac = max(0.0, min(1.0, used / window))
        color = t.meter_ok if frac < 0.6 else t.meter_mid if frac < 0.85 else t.meter_high
        filled = frac * cells
        full = int(filled)
        half = filled - full >= 0.5 or (used > 0 and full == 0)
        bar = [Span("━" * full, Style(fg=color))]
        if half and full < cells:
            bar.append(Span("╸", Style(fg=color)))
        rest = cells - full - (1 if half and full < cells else 0)
        bar.append(Span("─" * rest, Style(fg=t.meter_track)))
        pct = f" {frac * 100:.0f}%"
        out = [*bar, Span(pct, Style(fg=color)), Span(f" of {_tokens(window)}", t.faint)]
        if usage.cached_tokens and used:  # how much of the last prompt the provider served from its cache
            out.append(Span(f" · {min(100, round(usage.cached_tokens * 100 / used))}% cached", t.faint))
        if usage.total_cost >= 0.0005:
            out.append(Span(f"  ${usage.total_cost:.2f}", t.faint))
        return out

    # ── the real terminal loop ───────────────────────────────────────────────

    def run(self, terminal: Terminal, *, theme_override: Literal["dark", "light"] | None = None) -> None:
        self.terminal = terminal
        terminal.start(title=f"frond · {self.workspace.root.name}")
        try:
            bg = terminal.query_background()
            dark = (luminance(bg) < 0.4) if bg is not None else True
            if theme_override is not None:
                dark = theme_override == "dark"
            self.theme = make_theme(dark=dark, background=bg)
            self.md = MarkdownRenderer(self.theme, self._link_for)
            for block in self.blocks:
                block.touch()
            self.renderer = Renderer(self.color_mode)
            terminal.on_resume = self._renderer_invalidate
            last_tick = last_render = 0.0
            failures = 0
            while not self.should_quit:
                try:
                    last_tick, last_render = self._iterate(terminal, last_tick, last_render)
                    failures = 0
                except Exception as exc:  # keep the session alive through a UI bug; it is logged
                    failures += 1
                    logging.getLogger("frond.tui").exception("UI error")
                    if failures > 20:
                        raise
                    self.add(NoticeBlock("error", f"UI error (details in the log): {exc!r}"))
                    self._renderer_invalidate()
        finally:
            self.should_quit = True
            self.decline_pending_approvals()
            terminal.stop()

    def _iterate(self, terminal: Terminal, last_tick: float, last_render: float) -> tuple[float, float]:
        """One turn of the event loop: read input, apply agent events, and render at most 60 times a second."""
        now = time.monotonic()
        animate = self.running or (self.flash_text and now < self.flash_until)
        timeout = 0.02 if self.decoder.pending() else (0.08 if animate else 0.5)
        if self.dirty:
            timeout = min(timeout, max(0.0, FRAME_INTERVAL - (now - last_render)))
        data = terminal.read(timeout)
        if data:
            for event in self.decoder.feed(data):
                self.on_input(event)
        elif self.decoder.pending():
            for event in self.decoder.flush():
                self.on_input(event)
        if self.pump():
            self.dirty = True
        if terminal.resized:
            terminal.resized = False
            self._renderer_invalidate()
            self.dirty = True
        now = time.monotonic()
        if now - last_tick >= 0.08:
            last_tick = now
            if animate:
                self.tick += 1
                self.dirty = True
        if self.dirty and now - last_render >= FRAME_INTERVAL:
            cols, rows = terminal.size()
            frame = self.draw(cols, rows)
            terminal.write(self.renderer.render(frame, cursor_visible=self.approval is None))
            last_render = now
        return last_tick, last_render


def _tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1000:
        return f"{n / 1000:.0f}k"
    return str(n)


def _display_path(path: Path) -> str:
    home = Path.home()
    try:
        return "~/" + path.relative_to(home).as_posix()
    except ValueError:
        return path.as_posix()
