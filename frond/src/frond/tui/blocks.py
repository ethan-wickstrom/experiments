"""Transcript blocks: what a conversation looks like on screen.

Each block renders itself to a list of styled lines for a given width and caches the result; only blocks
that animate (a running step's spinner, a live command) re-render on every frame.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Literal

from frond.events import ChangeKind, CommandStatus, PlanItem, TurnStatus
from frond.tui.highlight import highlight, language_for
from frond.tui.markdown import MarkdownRenderer
from frond.tui.style import PLAIN, Style, Theme
from frond.tui.text import (
    Line,
    Span,
    line_width,
    pad,
    sanitize,
    styled,
    truncate,
    wrap,
    wrap_text,
)

SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
_HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")
_SUBMIT_ONLY = re.compile(r"\A\s*(?:#[^\n]*\n\s*)*SUBMIT\(", re.S)


@dataclass
class Ctx:
    theme: Theme
    md: MarkdownRenderer
    details: bool = False
    tick: int = 0
    now: float = field(default_factory=time.monotonic)

    def spinner(self) -> str:
        return SPINNER[self.tick % len(SPINNER)]


def fmt_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms" if seconds >= 0.001 else "0s"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m {secs:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


def right_align(left: Line, right: Line, width: int, fill: Style = PLAIN) -> Line:
    """``left`` then ``right`` flush against the right edge; ``left`` is truncated if needed."""
    rw = line_width(right)
    left = truncate(left, max(1, width - rw - 1))
    gap = width - line_width(left) - rw
    return [*left, Span(" " * max(1, gap), fill), *right]


def panel_line(
    content: Line, width: int, theme: Theme, *, bar: Style | None = None, bg: tuple[int, int, int] | None = None
) -> Line:
    """A row on a card: optional coloured left bar, content on the panel background, padded to width."""
    color = bg or theme.panel
    base = Style(bg=color)
    head = [Span("▎", (bar or theme.faint) + base)] if bar is not None else [Span(" ", base)]
    body = [Span(s.text, base + s.style) for s in content]
    return pad([*head, Span(" ", base), *truncate(body, width - 2)], width, base)


class Block:
    animated = False

    def __init__(self) -> None:
        self.version = 0
        self.expanded = False
        self._cache: tuple[tuple[object, ...], list[Line]] | None = None

    def touch(self) -> None:
        self.version += 1

    def toggle(self) -> bool:
        self.expanded = not self.expanded
        self.touch()
        return True

    def lines(self, width: int, ctx: Ctx) -> list[Line]:
        key = (width, self.version, ctx.details, ctx.theme.name, ctx.tick if self.animated else -1)
        if self._cache is not None and self._cache[0] == key:
            return self._cache[1]
        out = self.render(width, ctx)
        self._cache = (key, out)
        return out

    def render(self, width: int, ctx: Ctx) -> list[Line]:
        raise NotImplementedError


# ── simple blocks ────────────────────────────────────────────────────────────


class WelcomeBlock(Block):
    def __init__(self, model: str, sub_model: str, location: str, branch: str | None, note: str | None = None) -> None:
        super().__init__()
        self.model, self.sub_model, self.location, self.branch, self.note = model, sub_model, location, branch, note

    def render(self, width: int, ctx: Ctx) -> list[Line]:
        t = ctx.theme
        models = self.model if self.sub_model == self.model else f"{self.model}  ·  sub-queries {self.sub_model}"
        where = self.location + (f"  ·  ⎇ {self.branch}" if self.branch else "")
        out = [
            [Span("◆ ", t.accent_bold), Span("frond", Style(bold=True)), Span("  recursive coding agent", t.muted)],
            [Span("  "), *truncate(styled(models, t.muted), width - 2)],
            [Span("  "), *truncate(styled(where, t.muted), width - 2)],
        ]
        if self.note:
            out += wrap_text(self.note, width, t.warn, prefix=[Span("  ")])
        out.append(
            [
                Span("  "),
                *truncate(
                    styled("⏎ send · @ attach files · / commands · esc stop · ctrl+o details", t.faint), width - 2
                ),
            ]
        )
        return out


class UserBlock(Block):
    def __init__(
        self, text: str, attachments: tuple[str, ...] = (), *, steer: Literal["", "sent", "read"] = ""
    ) -> None:
        super().__init__()
        self.text, self.attachments = text, attachments
        self.steer = steer  # a message sent into a running turn: "sent", then "read" once the model has it
        self.step = 0

    def render(self, width: int, ctx: Ctx) -> list[Line]:
        t = ctx.theme
        bar = [Span("▌ ", t.user_bar)]
        out: list[Line] = []
        for raw in sanitize(self.text).split("\n"):
            parts = re.split(r"((?<!\S)@\S+)", raw)
            line = [Span(p, t.accent if p.startswith("@") else Style(bold=True)) for p in parts if p]
            out += wrap(line, width, prefix=bar, continuation=bar)
        if self.attachments:
            out.append([*bar, *truncate(styled("⧉ " + "  ".join(self.attachments), t.muted), width - 2)])
        if self.steer == "sent":
            out.append([*bar, Span("↪ sent to the running turn · read before its next step", t.faint)])
        elif self.steer == "read":
            out.append([*bar, Span(f"↪ read before step {self.step}", t.faint)])
        return out


class NoticeBlock(Block):
    def __init__(self, level: Literal["info", "warn", "error"], text: str) -> None:
        super().__init__()
        self.level, self.text = level, text

    def render(self, width: int, ctx: Ctx) -> list[Line]:
        t = ctx.theme
        style, glyph = {"info": (t.muted, "·"), "warn": (t.warn, "!"), "error": (t.error, "✗")}[self.level]
        return wrap_text(self.text, width, style, prefix=[Span(glyph + " ", style)], continuation=[Span("  ")])


class TurnFooter(Block):
    def __init__(self, status: TurnStatus, steps: int, duration: float, error: str | None, cost: float | None) -> None:
        super().__init__()
        self.status, self.steps, self.duration, self.error, self.cost = status, steps, duration, error, cost

    def render(self, width: int, ctx: Ctx) -> list[Line]:
        t = ctx.theme
        glyph, label, style = {
            "done": ("✓", "done", t.success),
            "limit": ("◐", "step limit reached", t.warn),
            "cancelled": ("■", "stopped", t.warn),
            "error": ("✗", "failed", t.error),
        }[self.status]
        parts = [label, f"{self.steps} step{'s' if self.steps != 1 else ''}", fmt_duration(self.duration)]
        if self.cost:
            parts.append(f"${self.cost:.3f}" if self.cost < 1 else f"${self.cost:.2f}")
        out: list[Line] = [[Span(glyph + " ", style), Span(" · ".join(parts), t.faint)]]
        if self.error:
            out += wrap_text(self.error, width, t.error, prefix=[Span("  ")], continuation=[Span("  ")])
        return out


class ResponseBlock(Block):
    def __init__(self) -> None:
        super().__init__()
        self.text = ""
        self.streaming = True

    @property
    def animated(self) -> bool:  # type: ignore[override]
        return self.streaming

    def render(self, width: int, ctx: Ctx) -> list[Line]:
        t = ctx.theme
        body = ctx.md.render(self.text, width - 2) if self.text.strip() else []
        out: list[Line] = []
        for i, line in enumerate(body):
            out.append([Span("◆ " if i == 0 else "  ", t.accent_bold), *line])
        if self.streaming:
            cursor = [Span("  " if out else "◆ ", t.accent_bold), Span(ctx.spinner(), t.accent)]
            if out and line_width(out[-1]) + 2 < width:
                out[-1] = [*out[-1], Span(" "), Span(ctx.spinner(), t.accent)]
            else:
                out.append(cursor)
        return out


class PlanBlock(Block):
    def __init__(self, items: tuple[PlanItem, ...]) -> None:
        super().__init__()
        self.items = items

    def render(self, width: int, ctx: Ctx) -> list[Line]:
        t = ctx.theme
        done = sum(1 for i in self.items if i.status == "done")
        out: list[Line] = [
            [Span("☰ ", t.accent), Span("plan", Style(bold=True)), Span(f"  {done}/{len(self.items)}", t.faint)]
        ]
        for item in self.items:
            glyph, gstyle, tstyle = {
                "done": ("✓", t.success, t.faint),
                "active": ("▸", t.accent_bold, Style(bold=True)),
                "todo": ("○", t.faint, t.muted),
            }[item.status]
            out += wrap(
                styled(item.text, tstyle),
                width,
                prefix=[Span("  "), Span(glyph + " ", gstyle)],
                continuation=[Span("    ")],
            )
        return out


# ── activity items inside a step ─────────────────────────────────────────────


class Item:
    """Something a step did. Compact items share lines; cards get their own rows."""

    compact = False
    animated = False
    expanded = False

    def toggle(self) -> None:
        self.expanded = not self.expanded

    def chip(self, ctx: Ctx) -> Line:
        return []

    def render(self, width: int, ctx: Ctx, details: bool) -> list[Line]:
        return []


class ViewItem(Item):
    compact = True

    def __init__(self, path: str, start: int, end: int, total: int) -> None:
        self.path, self.start, self.end, self.total = path, start, end, total

    def chip(self, ctx: Ctx) -> Line:
        t = ctx.theme
        whole = self.start <= 1 and self.end >= self.total
        rng = "" if whole else f":{self.start}-{self.end}"
        return [Span("read ", t.faint), Span(self.path, t.muted), Span(rng, t.faint)]


class SearchItem(Item):
    compact = True

    def __init__(self, kind: str, query: str, count: int) -> None:
        self.kind, self.query, self.count = kind, query, count

    def chip(self, ctx: Ctx) -> Line:
        t = ctx.theme
        q = self.query if len(self.query) <= 48 else self.query[:47] + "…"
        if self.kind == "ls":
            return [Span("ls ", t.faint), Span(q, t.muted)]
        if self.kind == "fetch":
            return [Span("fetch ", t.faint), Span(q, t.muted)]
        noun = "match" if self.kind == "grep" else "file"
        plural = "" if self.count == 1 else ("es" if noun == "match" else "s")
        return [Span(f"{self.kind} ", t.faint), Span(q, t.muted), Span(f" {self.count} {noun}{plural}", t.faint)]


class SubQueryItem(Item):
    compact = True

    def __init__(self, total: int) -> None:
        self.total, self.done = total, 0

    @property
    def animated(self) -> bool:  # type: ignore[override]
        return self.done < self.total

    def chip(self, ctx: Ctx) -> Line:
        t = ctx.theme
        label = "llm_query" if self.total == 1 else f"llm_query ×{self.total}"
        if self.done < self.total:
            return [
                Span(ctx.spinner() + " ", t.accent),
                Span(label, t.muted),
                Span(f" {self.done}/{self.total}", t.faint),
            ]
        return [Span(label, t.muted), Span(" ✓", t.success)]


class DiffCard(Item):
    def __init__(self, path: str, kind: ChangeKind, diff: str, added: int, removed: int, old_path: str | None) -> None:
        self.path, self.kind, self.diff, self.added, self.removed, self.old_path = (
            path,
            kind,
            diff,
            added,
            removed,
            old_path,
        )

    def render(self, width: int, ctx: Ctx, details: bool) -> list[Line]:
        t = ctx.theme
        stats: Line = []
        if self.added:
            stats.append(Span(f"+{self.added}", t.success))
        if self.removed:
            stats += [Span(" " if stats else ""), Span(f"−{self.removed}", t.error)]
        verb = {"create": ("✚", "created"), "edit": ("✎", ""), "delete": ("✖", "deleted"), "move": ("→", "moved")}
        glyph, word = verb[self.kind]
        title: Line = [Span(glyph + " ", t.accent), Span(self.path, Style(bold=True))]
        if word:
            title.append(Span(f"  {word}", t.faint))
        if self.kind == "move":
            return [
                [
                    Span("→ ", t.accent),
                    Span(self.old_path or "", t.muted),
                    Span(" → ", t.faint),
                    Span(self.path, Style(bold=True)),
                ]
            ]
        out = [right_align(title, stats, width)]
        if self.kind == "delete" or not self.diff or self.diff.startswith("("):
            if self.diff.startswith("("):
                out.append(panel_line(styled(self.diff, t.faint), width, t))
            return out
        rows = self._rows(ctx)
        limit = len(rows) if (details or self.expanded) else (14 if self.kind == "create" else 24)
        out.extend(self._fit(row, width, ctx) for row in rows[:limit])
        if len(rows) > limit:
            more = len(rows) - limit
            out.append(
                panel_line(
                    styled(f"… {more} more line{'s' if more != 1 else ''}  (click to expand)", t.faint), width, t
                )
            )
        return out

    def _rows(self, ctx: Ctx) -> list[tuple[str, str | None, str]]:
        """(kind, line number, text) rows parsed from the unified diff."""
        rows: list[tuple[str, str | None, str]] = []
        old_no = new_no = 0
        first_hunk = True
        for line in self.diff.split("\n"):
            if line.startswith(("---", "+++")):
                continue
            m = _HUNK.match(line)
            if m:
                old_no, new_no = int(m.group(1)), int(m.group(2))
                if not first_hunk:
                    rows.append(("gap", None, ""))
                first_hunk = False
                continue
            if line.startswith("+"):
                rows.append(("add", str(new_no), line[1:]))
                new_no += 1
            elif line.startswith("-"):
                rows.append(("del", str(old_no), line[1:]))
                old_no += 1
            elif line.startswith("\\"):
                continue
            else:
                rows.append(("ctx", str(new_no), line[1:] if line.startswith(" ") else line))
                old_no += 1
                new_no += 1
        return rows

    def _fit(self, row: tuple[str, str | None, str], width: int, ctx: Ctx) -> Line:
        t = ctx.theme
        kind, number, text = row
        if kind == "gap":
            return panel_line(styled("⋯", t.faint), width, t)
        style = {"add": t.add, "del": t.remove, "ctx": Style(bg=t.panel)}[kind]
        if self.kind == "create":
            style = Style(bg=t.panel)  # a new file is all additions: markers suffice, a solid tint is just noise
        bg = style.bg or t.panel
        base = Style(bg=bg)
        mark = {"add": "+", "del": "−", "ctx": " "}[kind]
        lang = language_for(self.path)
        code = highlight(text, lang, ctx.theme.syntax, base)[0] if lang else styled(sanitize(text), base)
        if kind == "del":
            code = [Span(s.text, s.style + Style(fg=t.remove.fg)) for s in code] if not lang else code
        gutter = [
            Span(" ", base),
            Span(f"{number or '':>4} ", base + t.faint),
            Span(mark + " ", base + (t.success if kind == "add" else t.error if kind == "del" else t.faint)),
        ]
        line = [*gutter, *[Span(s.text, base + s.style) for s in code]]
        return pad(truncate(line, width), width, base)


class CommandCard(Item):
    def __init__(self, cmd_id: int, command: str, background: bool) -> None:
        self.cmd_id, self.command, self.background = cmd_id, command, background
        self.output = ""
        self.status: CommandStatus | None = None
        self.exit_code: int | None = None
        self.duration = 0.0
        self.started = time.monotonic()

    @property
    def animated(self) -> bool:  # type: ignore[override]
        return self.status is None

    def render(self, width: int, ctx: Ctx, details: bool) -> list[Line]:
        t = ctx.theme
        if self.status is None:
            right = [Span(ctx.spinner() + " ", t.accent), Span(fmt_duration(ctx.now - self.started), t.faint)]
        elif self.status == "background":
            right = [Span("⧗ background", t.info)]
        elif self.status == "ok":
            right = [Span("✓ ", t.success), Span(fmt_duration(self.duration), t.faint)]
        elif self.status == "failed":
            right = [Span(f"✗ exit {self.exit_code}", t.error), Span(f" · {fmt_duration(self.duration)}", t.faint)]
        elif self.status == "timeout":
            right = [Span("⏱ timed out", t.warn), Span(f" · {fmt_duration(self.duration)}", t.faint)]
        else:
            right = [Span("■ stopped", t.warn)]
        command = sanitize(self.command).replace("\n", " ⏎ ")
        title = [Span("$ ", t.accent_bold), *highlight(command, "shell", t.syntax, Style(bold=True))[0]]
        out = [right_align(title, right, width)]
        lines = sanitize(self.output.rstrip("\n")).split("\n") if self.output.strip() else []
        if not lines:
            return out
        if details or self.expanded:
            shown, hidden = lines[-400:], max(0, len(lines) - 400)
        else:
            keep = 10 if self.status is None else 8
            shown, hidden = lines[-keep:], max(0, len(lines) - keep)
        if hidden:
            out.append(panel_line(styled(f"… {hidden} earlier line{'s' if hidden != 1 else ''}", t.faint), width, t))
        out.extend(panel_line(_status_tokens(line, t), width, t) for line in shown)
        return out


_STATUS_WORDS = re.compile(
    r"\b(?:(?P<bad>FAILED|FAILURES?|ERRORS?|Error|error|failed|Traceback|Exception|panic|FAIL)|"
    r"(?P<good>PASSED|passed|OK|ok|succeeded|success|SUCCESS|done))\b"
)


def _status_tokens(line: str, t: Theme) -> Line:
    """Muted command output with only the status words coloured, so failures stand out without a wall of colour."""
    out: Line = []
    pos = 0
    for m in _STATUS_WORDS.finditer(line):
        if m.start() > pos:
            out.append(Span(line[pos : m.start()], t.muted))
        out.append(Span(m.group(), t.error if m.group("bad") else t.success))
        pos = m.end()
    if pos < len(line):
        out.append(Span(line[pos:], t.muted))
    return out


class SubAgentCard(Item):
    def __init__(self, agent_id: int, task: str) -> None:
        self.agent_id, self.task = agent_id, task
        self.step = 0
        self.activity = "starting"
        self.result: str | None = None
        self.ok = True
        self.started = time.monotonic()
        self.duration = 0.0

    @property
    def animated(self) -> bool:  # type: ignore[override]
        return self.result is None

    def render(self, width: int, ctx: Ctx, details: bool) -> list[Line]:
        t = ctx.theme
        if self.result is None:
            right = [Span(ctx.spinner() + " ", t.accent), Span(f"step {self.step}", t.faint)]
        elif self.ok:
            right = [Span("✓ ", t.success), Span(f"{self.step} steps · {fmt_duration(self.duration)}", t.faint)]
        else:
            right = [Span("✗ failed", t.error)]
        title = [Span("◇ ", t.info), Span("subagent ", Style(bold=True)), *styled(self.task.split("\n")[0], t.muted)]
        out = [right_align(title, right, width)]
        if self.result is None:
            out.append(panel_line(styled(self.activity, t.faint), width, t, bar=t.info))
        else:
            report = self.result.strip().split("\n")
            limit = len(report) if (details or self.expanded) else 3
            out.extend(panel_line(styled(line, t.muted), width, t, bar=t.info) for line in report[:limit])
            if len(report) > limit:
                out.append(panel_line(styled(f"… {len(report) - limit} more lines", t.faint), width, t, bar=t.info))
        return out


# ── the step block ───────────────────────────────────────────────────────────

type StepState = Literal["thinking", "writing", "running", "done", "error", "final", "stopped"]


class StepBlock(Block):
    def __init__(self, step: int, max_steps: int) -> None:
        super().__init__()
        self.step, self.max_steps = step, max_steps
        self.reasoning = ""
        self.thinking = ""
        self.code = ""
        self.state: StepState = "thinking"
        self.items: list[Item] = []
        self.output = ""
        self.error: str | None = None
        self.duration = 0.0
        self.started = time.monotonic()
        self._item_rows: list[tuple[int, int, Item]] = []

    @property
    def animated(self) -> bool:  # type: ignore[override]
        return self.state in ("thinking", "writing", "running") or any(i.animated for i in self.items)

    @property
    def is_submit(self) -> bool:
        return bool(_SUBMIT_ONLY.match(self.code))

    def code_body(self) -> str:
        code = self.code.strip("\n")
        if code.startswith("```"):
            code = code.split("\n", 1)[1] if "\n" in code else ""
        if code.rstrip().endswith("```"):
            code = code.rstrip()[:-3]
        return code.rstrip()

    def render(self, width: int, ctx: Ctx) -> list[Line]:
        t = ctx.theme
        out: list[Line] = []
        live = self.state in ("thinking", "writing", "running")
        bullet = [Span(ctx.spinner() if self.state == "thinking" else "∙", t.accent if live else t.faint), Span(" ")]
        if self.reasoning.strip():
            out += wrap_text(self.reasoning.strip(), width, t.muted, prefix=bullet, continuation=[Span("  ")])
        elif self.state == "thinking":
            label = "thinking" + (f" · {len(self.thinking.split())} words" if self.thinking else "")
            out.append([*bullet, Span(label, t.faint)])
        submit = self.is_submit
        code = self.code_body()
        if code and not (submit and self.state in ("final", "writing", "running", "done")):
            out += self._code_panel(code, width, ctx)
        out += self._items(width, ctx, len(out))
        if self.state == "error" and self.error:
            lines = sanitize(self.error).strip().split("\n")
            shown = lines if (ctx.details or self.expanded) else lines[-6:]
            if len(lines) > len(shown):
                out.append([Span("  ╰ ", t.faint), Span(f"… {len(lines) - len(shown)} lines", t.faint)])
            for i, line in enumerate(shown):
                out += wrap(
                    styled(line, t.error),
                    width,
                    prefix=[Span("  ╰ " if i == 0 and len(lines) == len(shown) else "    ", t.faint)],
                    continuation=[Span("    ")],
                )
        elif self.output.strip() and not submit:
            out += self._output(width, ctx)
        return out

    def _code_panel(self, code: str, width: int, ctx: Ctx) -> list[Line]:
        t = ctx.theme
        streaming = self.state == "writing"
        full = ctx.details or self.expanded
        total = code.count("\n") + 1
        limit = total if full else (12 if streaming else 8)
        hidden = max(0, total - limit)
        if streaming and hidden:
            # Re-highlighting a long block on every frame is the hot path while code streams in; only the tail
            # is visible, so highlight that (with some lines of lead-in for context).
            source = "\n".join(code.split("\n")[-(limit + 40) :])
            shown = highlight(source, "python", t.syntax, Style(bg=t.panel))[-limit:]
        else:
            rows = highlight(code, "python", t.syntax, Style(bg=t.panel))
            shown = rows[:limit]
        label = self._label(ctx)
        out: list[Line] = []
        if streaming and hidden:
            out.append(panel_line(styled(f"… {hidden} lines above", t.faint), width, t, bar=t.faint))
        for i, row in enumerate(shown):
            line = panel_line(row, width, t, bar=t.accent if streaming else t.faint)
            if i == 0 and label:
                body = truncate(row, max(4, width - 4 - line_width(label)))
                line = panel_line(
                    [*pad(body, width - 3 - line_width(label), Style(bg=t.panel)), *label],
                    width,
                    t,
                    bar=t.accent if streaming else t.faint,
                )
            out.append(line)
        if hidden and not streaming:
            out.append(
                panel_line(styled(f"… {hidden} more line{'s' if hidden != 1 else ''}", t.faint), width, t, bar=t.faint)
            )
        return out

    def _label(self, ctx: Ctx) -> Line:
        t = ctx.theme
        base = Style(bg=t.panel)
        if self.state == "running":
            return [
                Span(ctx.spinner() + " ", base + t.accent),
                Span(fmt_duration(ctx.now - self.started), base + t.faint),
            ]
        if self.state == "writing":
            return [Span(f"step {self.step}", base + t.faint)]
        if self.state == "error":
            return [Span(f"{self.step} ", base + t.faint), Span("✗", base + t.error)]
        if self.state == "stopped":
            return [Span(f"{self.step} ", base + t.faint), Span("■", base + t.warn)]
        return [Span(f"{self.step} · {fmt_duration(self.duration)}", base + t.faint)]

    def _items(self, width: int, ctx: Ctx, offset: int) -> list[Line]:
        t = ctx.theme
        out: list[Line] = []
        chips: list[Line] = []
        self._item_rows = []

        def flush() -> None:
            if not chips:
                return
            joined: Line = []
            for i, chip in enumerate(chips):
                if i:
                    joined.append(Span("  ·  ", t.faint))
                joined += chip
            out.extend(wrap(joined, width, prefix=[Span("  ↳ ", t.faint)], continuation=[Span("    ")]))
            chips.clear()

        for item in self.items:
            if item.compact:
                chips.append(item.chip(ctx))
                continue
            flush()
            start = offset + len(out)
            out += [[Span("  "), *row] for row in item.render(width - 2, ctx, ctx.details)]
            self._item_rows.append((start, offset + len(out), item))
        flush()
        return out

    def _output(self, width: int, ctx: Ctx) -> list[Line]:
        t = ctx.theme
        lines = sanitize(self.output.rstrip()).split("\n")
        full = ctx.details or self.expanded
        has_cards = any(not item.compact for item in self.items)
        if has_cards and not full:
            # The cards above already show what happened; the printed output is mostly for the model.
            noun = "line" if len(lines) == 1 else "lines"
            return [[Span("  ╰ ", t.faint), Span(f"{len(lines)} {noun} of output", t.faint)]]
        keep = len(lines) if full else (4 if self.state == "running" else 3)
        out: list[Line] = []
        if self.state == "running" and len(lines) > keep:
            # Live output: show the newest lines, which is where progress shows up.
            out.append([Span("  ╰ ", t.faint), Span(f"… {len(lines) - keep} earlier lines", t.faint)])
            out.extend([Span("    "), *truncate(styled(line, t.muted), width - 4)] for line in lines[-keep:])
            return out
        for i, line in enumerate(lines[:keep]):
            prefix = "  ╰ " if i == 0 else "    "
            out += [[Span(prefix, t.faint), *truncate(styled(line, t.faint), width - 4)]]
        if len(lines) > keep:
            out.append([Span("    "), Span(f"… {len(lines) - keep} more lines of output", t.faint)])
        return out

    def click(self, row: int) -> bool:
        """Toggle whatever was rendered at ``row``: a card, or else the step's own code and output."""
        for start, end, item in self._item_rows:
            if start <= row < end:
                item.toggle()
                self.touch()
                return True
        return self.toggle()
