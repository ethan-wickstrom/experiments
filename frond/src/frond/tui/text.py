"""Measuring, wrapping and truncating styled text in terminal cells."""

from __future__ import annotations

import functools
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

from frond.tui.style import PLAIN, Style

_ZERO_WIDTH = frozenset({0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF})


@functools.lru_cache(maxsize=65536)
def char_width(ch: str) -> int:
    o = ord(ch)
    if 32 <= o < 127:
        return 1
    if o < 32 or 0x7F <= o < 0xA0 or o in _ZERO_WIDTH or 0xFE00 <= o <= 0xFE0F or 0xE0100 <= o <= 0xE01EF:
        return 0
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def str_width(s: str) -> int:
    if s.isascii() and s.isprintable():
        return len(s)
    return sum(char_width(c) for c in s)


@dataclass(frozen=True, slots=True)
class Span:
    text: str
    style: Style = PLAIN


type Line = list[Span]


def line_width(line: Iterable[Span]) -> int:
    return sum(str_width(s.text) for s in line)


def line_text(line: Iterable[Span]) -> str:
    return "".join(s.text for s in line)


def styled(text: str, style: Style = PLAIN) -> Line:
    return [Span(text, style)] if text else []


def restyle(line: Line, style: Style) -> Line:
    """Overlay ``style`` on every span (e.g. to put a line on a panel background)."""
    return [Span(s.text, s.style + style) for s in line]


def sanitize(text: str) -> str:
    """Make arbitrary text safe to put on screen: expand tabs, drop control characters except newlines."""
    if "\t" in text:
        text = text.expandtabs(4)
    if text.isascii() and text.isprintable():
        return text
    return "".join(c for c in text if c == "\n" or (ord(c) >= 32 and not (0x7F <= ord(c) < 0xA0)))


def truncate(line: Line, width: int, ellipsis: str = "…") -> Line:
    if width <= 0:
        return []
    if line_width(line) <= width:
        return line
    budget = width - str_width(ellipsis)
    out: Line = []
    used = 0
    last_style = PLAIN
    for span in line:
        last_style = span.style
        chunk = []
        for ch in span.text:
            w = char_width(ch)
            if used + w > budget:
                break
            chunk.append(ch)
            used += w
        else:
            out.append(span)
            continue
        if chunk:
            out.append(Span("".join(chunk), span.style))
        break
    out.append(Span(ellipsis, last_style))
    return out


def _tokens(line: Line) -> list[tuple[bool, list[tuple[str, Style]]]]:
    """Split a styled line into alternating (is_space, [(char, style)...]) runs."""
    tokens: list[tuple[bool, list[tuple[str, Style]]]] = []
    for span in line:
        for ch in span.text:
            space = ch == " "
            if tokens and tokens[-1][0] == space:
                tokens[-1][1].append((ch, span.style))
            else:
                tokens.append((space, [(ch, span.style)]))
    return tokens


def _join(cells: list[tuple[str, Style]]) -> Line:
    out: Line = []
    for ch, style in cells:
        if out and out[-1].style == style:
            out[-1] = Span(out[-1].text + ch, style)
        else:
            out.append(Span(ch, style))
    return out


def wrap(line: Line, width: int, *, prefix: Line | None = None, continuation: Line | None = None) -> list[Line]:
    """Word-wrap a styled line to ``width`` cells.

    ``prefix`` starts the first output line and ``continuation`` every following one (hanging indents,
    list bullets, quote bars); both count toward the width. Words longer than a line are split.
    """
    prefix = prefix or []
    continuation = continuation if continuation is not None else [Span(" " * line_width(prefix))]
    first_room = max(1, width - line_width(prefix))
    rest_room = max(1, width - line_width(continuation))
    rows: list[list[tuple[str, Style]]] = [[]]
    used = 0
    room = first_room

    def newline() -> None:
        nonlocal used, room
        while rows[-1] and rows[-1][-1][0] == " ":
            rows[-1].pop()
        rows.append([])
        used = 0
        room = rest_room

    for is_space, cells in _tokens(line):
        w = sum(char_width(c) for c, _ in cells)
        if is_space:
            if used == 0 and len(rows) > 1:
                continue  # no leading spaces on wrapped lines
            if used + w > room:
                newline()
                continue
            rows[-1].extend(cells)
            used += w
            continue
        if used + w <= room:
            rows[-1].extend(cells)
            used += w
            continue
        if w <= rest_room and used > 0:
            newline()
            rows[-1].extend(cells)
            used += w
            continue
        for cell in cells:  # hard-split a long word
            cw = char_width(cell[0])
            if used + cw > room:
                newline()
            rows[-1].append(cell)
            used += cw
    out: list[Line] = []
    for i, row in enumerate(rows):
        while row and row[-1][0] == " ":
            row.pop()
        out.append([*(prefix if i == 0 else continuation), *_join(row)])
    return out


def wrap_text(
    text: str, width: int, style: Style = PLAIN, *, prefix: Line | None = None, continuation: Line | None = None
) -> list[Line]:
    """Wrap plain text (possibly multi-line) in one style; blank lines are preserved."""
    out: list[Line] = []
    for i, raw in enumerate(sanitize(text).split("\n")):
        out.extend(
            wrap(styled(raw, style), width, prefix=prefix if i == 0 else continuation, continuation=continuation)
        )
    return out


def pad(line: Line, width: int, style: Style = PLAIN) -> Line:
    gap = width - line_width(line)
    return [*line, Span(" " * gap, style)] if gap > 0 else line
