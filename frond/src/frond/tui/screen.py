"""A cell buffer and a diffing renderer that turns it into minimal terminal output."""

from __future__ import annotations

from collections.abc import Iterable

from frond.tui.style import PLAIN, ColorMode, Style, sgr
from frond.tui.text import Span, char_width

WIDE_TAIL = ""  # marks the second cell of a double-width character


class Buffer:
    def __init__(self, width: int, height: int, style: Style = PLAIN) -> None:
        self.width = width
        self.height = height
        self.chars: list[list[str]] = [[" "] * width for _ in range(height)]
        self.styles: list[list[Style]] = [[style] * width for _ in range(height)]
        self.cursor: tuple[int, int] | None = None

    def _clear_wide(self, x: int, y: int) -> None:
        row = self.chars[y]
        if row[x] == WIDE_TAIL and x > 0:
            row[x - 1] = " "
        if x + 1 < self.width and row[x + 1] == WIDE_TAIL:
            row[x + 1] = " "

    def put(self, x: int, y: int, text: str, style: Style = PLAIN, max_x: int | None = None) -> int:
        """Write ``text`` at (x, y) without wrapping; returns the x after the last cell written."""
        if not 0 <= y < self.height:
            return x
        limit = self.width if max_x is None else min(max_x, self.width)
        chars, styles = self.chars[y], self.styles[y]
        for ch in text:
            w = char_width(ch)
            if w == 0:
                if x > 0 and x - 1 < limit and chars[x - 1] not in ("", " "):
                    chars[x - 1] += ch  # combining mark joins the previous cell
                continue
            if x >= limit:
                break
            if x < 0:
                x += w
                continue
            if w == 2 and x + 1 >= limit:
                self._clear_wide(x, y)
                chars[x], styles[x] = " ", style
                x += 1
                break
            self._clear_wide(x, y)
            chars[x], styles[x] = ch, style
            if w == 2:
                self._clear_wide(x + 1, y)
                chars[x + 1], styles[x + 1] = WIDE_TAIL, style
            x += w
        return x

    def put_line(
        self, x: int, y: int, line: Iterable[Span], max_x: int | None = None, base: Style | None = None
    ) -> int:
        for span in line:
            x = self.put(x, y, span.text, span.style if base is None else base + span.style, max_x)
        return x

    def fill(self, x: int, y: int, w: int, h: int, style: Style = PLAIN, char: str = " ") -> None:
        for row in range(max(0, y), min(self.height, y + h)):
            for col in range(max(0, x), min(self.width, x + w)):
                self.chars[row][col] = char
                self.styles[row][col] = style

    def paint(self, x: int, y: int, w: int, style: Style) -> None:
        """Overlay ``style`` on existing cells (e.g. a selection highlight) without changing text."""
        if not 0 <= y < self.height:
            return
        row = self.styles[y]
        for col in range(max(0, x), min(self.width, x + w)):
            row[col] = row[col] + style

    def text_rows(self) -> list[str]:
        return ["".join(c for c in row).rstrip() for row in self.chars]

    def dump(self) -> str:
        return "\n".join(self.text_rows())


class Renderer:
    """Emits only what changed since the previous frame."""

    def __init__(self, mode: ColorMode) -> None:
        self.mode = mode
        self.prev: Buffer | None = None

    def invalidate(self) -> None:
        self.prev = None

    def render(self, buf: Buffer, *, cursor_visible: bool = True) -> str:
        prev = self.prev
        full = prev is None or prev.width != buf.width or prev.height != buf.height
        out: list[str] = ["\x1b[?2026h\x1b[?25l"]
        if full:
            out.append("\x1b[0m\x1b[2J")
        current: Style | None = None
        link: str | None = None
        for y in range(buf.height):
            chars, styles = buf.chars[y], buf.styles[y]
            if not full and prev is not None and prev.chars[y] == chars and prev.styles[y] == styles:
                continue
            if full or prev is None:
                start, end = 0, buf.width
            else:
                pc, ps = prev.chars[y], prev.styles[y]
                start = 0
                while start < buf.width and pc[start] == chars[start] and ps[start] == styles[start]:
                    start += 1
                end = buf.width
                while end > start and pc[end - 1] == chars[end - 1] and ps[end - 1] == styles[end - 1]:
                    end -= 1
                if start > 0 and chars[start] == WIDE_TAIL:
                    start -= 1
                if end < buf.width and chars[end] == WIDE_TAIL:
                    end += 1
            out.append(f"\x1b[{y + 1};{start + 1}H")
            for x in range(start, end):
                ch = chars[x]
                if ch == WIDE_TAIL:
                    continue
                style = styles[x]
                if style is not current:
                    if style != current:
                        out.append(sgr(style, self.mode))
                    current = style
                if style.link != link:
                    out.append(f"\x1b]8;;{style.link or ''}\x1b\\")
                    link = style.link
                out.append(ch)
        if link:
            out.append("\x1b]8;;\x1b\\")
        out.append("\x1b[0m")
        if buf.cursor is not None and cursor_visible:
            cx, cy = buf.cursor
            out.append(f"\x1b[{cy + 1};{cx + 1}H\x1b[5 q\x1b[?25h")
        out.append("\x1b[?2026l")
        self.prev = buf
        return "".join(out)
