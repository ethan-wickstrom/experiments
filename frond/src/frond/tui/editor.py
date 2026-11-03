"""The prompt editor: a multi-line text buffer with a caret, readline-style editing, and history."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from frond.tui.text import char_width, str_width

_WORD = re.compile(r"\w+|[^\w\s]+")
MENTION = re.compile(r"(?:(?<=\s)|^)@([^\s@]*)$")


@dataclass(frozen=True, slots=True)
class VisualLine:
    start: int  # index into text of the first character on this row
    end: int  # index just past the last character (excluding a newline)
    text: str


@dataclass(frozen=True, slots=True)
class Token:
    kind: Literal["mention", "command"]
    start: int
    end: int
    query: str


class Editor:
    def __init__(self) -> None:
        self.text = ""
        self.cursor = 0
        self.history: list[str] = []
        self.history_index: int | None = None
        self.draft = ""
        self.kill_ring = ""
        self._undo: list[tuple[str, int]] = []
        self.goal_column: int | None = None

    # ── state ────────────────────────────────────────────────────────────────

    def set(self, text: str, cursor: int | None = None) -> None:
        self.text = text
        self.cursor = len(text) if cursor is None else max(0, min(cursor, len(text)))
        self.goal_column = None

    def clear(self) -> None:
        self._snapshot()
        self.set("")
        self.history_index = None

    def _snapshot(self) -> None:
        if not self._undo or self._undo[-1] != (self.text, self.cursor):
            self._undo.append((self.text, self.cursor))
            del self._undo[:-200]

    def undo(self) -> None:
        if self._undo:
            text, cursor = self._undo.pop()
            if (text, cursor) == (self.text, self.cursor) and self._undo:
                text, cursor = self._undo.pop()
            self.set(text, cursor)

    # ── editing ──────────────────────────────────────────────────────────────

    def insert(self, s: str) -> None:
        if not s:
            return
        if s.strip() or not self._undo:
            self._snapshot()
        self.text = self.text[: self.cursor] + s + self.text[self.cursor :]
        self.cursor += len(s)
        self.goal_column = None
        self.history_index = None

    def backspace(self) -> None:
        if self.cursor > 0:
            self._snapshot()
            self.text = self.text[: self.cursor - 1] + self.text[self.cursor :]
            self.cursor -= 1
        self.goal_column = None

    def delete(self) -> None:
        if self.cursor < len(self.text):
            self._snapshot()
            self.text = self.text[: self.cursor] + self.text[self.cursor + 1 :]
        self.goal_column = None

    def replace(self, start: int, end: int, s: str) -> None:
        self._snapshot()
        self.text = self.text[:start] + s + self.text[end:]
        self.cursor = start + len(s)
        self.goal_column = None

    def _word_left(self) -> int:
        i = self.cursor
        while i > 0 and self.text[i - 1].isspace():
            i -= 1
        while i > 0 and not self.text[i - 1].isspace() and (self.text[i - 1].isalnum() or self.text[i - 1] == "_"):
            i -= 1
        if i == self.cursor:
            while i > 0 and not self.text[i - 1].isspace() and not self.text[i - 1].isalnum():
                i -= 1
        return i

    def _word_right(self) -> int:
        i = self.cursor
        n = len(self.text)
        while i < n and self.text[i].isspace():
            i += 1
        m = _WORD.match(self.text, i)
        return m.end() if m else i

    def word_left(self) -> None:
        self.cursor = self._word_left()
        self.goal_column = None

    def word_right(self) -> None:
        self.cursor = self._word_right()
        self.goal_column = None

    def kill_word_left(self) -> None:
        start = self._word_left()
        if start < self.cursor:
            self._snapshot()
            self.kill_ring = self.text[start : self.cursor]
            self.text = self.text[:start] + self.text[self.cursor :]
            self.cursor = start

    def kill_word_right(self) -> None:
        end = self._word_right()
        if end > self.cursor:
            self._snapshot()
            self.kill_ring = self.text[self.cursor : end]
            self.text = self.text[: self.cursor] + self.text[end:]

    def _line_bounds(self) -> tuple[int, int]:
        start = self.text.rfind("\n", 0, self.cursor) + 1
        end = self.text.find("\n", self.cursor)
        return start, len(self.text) if end == -1 else end

    def home(self) -> None:
        self.cursor = self._line_bounds()[0]
        self.goal_column = None

    def end(self) -> None:
        self.cursor = self._line_bounds()[1]
        self.goal_column = None

    def kill_to_end(self) -> None:
        _start, end = self._line_bounds()
        if self.cursor == end and end < len(self.text):
            end += 1  # at end of line: join with the next line
        if end > self.cursor:
            self._snapshot()
            self.kill_ring = self.text[self.cursor : end]
            self.text = self.text[: self.cursor] + self.text[end:]

    def kill_to_start(self) -> None:
        start, _ = self._line_bounds()
        if start < self.cursor:
            self._snapshot()
            self.kill_ring = self.text[start : self.cursor]
            self.text = self.text[:start] + self.text[self.cursor :]
            self.cursor = start

    def yank(self) -> None:
        self.insert(self.kill_ring)

    def left(self) -> None:
        self.cursor = max(0, self.cursor - 1)
        self.goal_column = None

    def right(self) -> None:
        self.cursor = min(len(self.text), self.cursor + 1)
        self.goal_column = None

    # ── layout (soft wrap) and vertical movement ─────────────────────────────

    def layout(self, width: int) -> list[VisualLine]:
        """Soft-wrap the text to ``width`` cells, recording where each visual row starts in the text.

        Rows hold at most ``width - 1`` cells so the caret always has a cell to sit in at the end of a row.
        """
        width = max(4, width) - 1
        rows: list[VisualLine] = []
        start = 0
        for logical in self.text.split("\n"):
            if not logical:
                rows.append(VisualLine(start, start, ""))
            else:
                i = 0
                while i < len(logical):
                    used = 0
                    j = i
                    last_space = -1
                    while j < len(logical):
                        w = char_width(logical[j])
                        if used + w > width:
                            break
                        if logical[j] == " ":
                            last_space = j
                        used += w
                        j += 1
                    if j < len(logical) and logical[j] == " ":
                        j += 1  # the word fits exactly: keep the following space on this row
                    elif j < len(logical) and last_space > i:
                        j = last_space + 1  # break after a space when possible
                    rows.append(VisualLine(start + i, start + j, logical[i:j]))
                    i = j
            start += len(logical) + 1
        return rows

    def caret(self, width: int) -> tuple[int, int]:
        """(column, row) of the caret within the soft-wrapped layout."""
        rows = self.layout(width)
        for idx, row in enumerate(rows):
            nxt = rows[idx + 1].start if idx + 1 < len(rows) else None
            if row.start <= self.cursor < row.end or (self.cursor == row.end and nxt != row.end):
                col = str_width(self.text[row.start : self.cursor])
                if col >= width:  # after a trailing space at the edge: show the caret on a fresh row
                    return 0, idx + 1
                return col, idx
        return 0, len(rows) - 1

    def move_vertical(self, delta: int, width: int) -> bool:
        """Move the caret up/down a visual row; False if it is already on the first/last row."""
        rows = self.layout(width)
        col, row = self.caret(width)
        target = row + delta
        if not 0 <= target < len(rows):
            return False
        if self.goal_column is None:
            self.goal_column = col
        goal = self.goal_column
        line = rows[target]
        pos = line.start
        used = 0
        for ch in line.text:
            w = char_width(ch)
            if used + w > goal:
                break
            used += w
            pos += 1
        self.cursor = min(pos, line.end)
        return True

    def on_first_row(self, width: int) -> bool:
        return self.caret(width)[1] == 0

    def on_last_row(self, width: int) -> bool:
        return self.caret(width)[1] == len(self.layout(width)) - 1

    # ── history ──────────────────────────────────────────────────────────────

    def remember(self, text: str) -> None:
        if text.strip() and (not self.history or self.history[-1] != text):
            self.history.append(text)
        self.history_index = None

    def history_prev(self) -> bool:
        if not self.history:
            return False
        if self.history_index is None:
            self.draft = self.text
            self.history_index = len(self.history) - 1
        elif self.history_index > 0:
            self.history_index -= 1
        else:
            return False
        self.set(self.history[self.history_index])
        return True

    def history_next(self) -> bool:
        if self.history_index is None:
            return False
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.set(self.history[self.history_index])
        else:
            self.history_index = None
            self.set(self.draft)
        return True

    # ── completion context ───────────────────────────────────────────────────

    def token(self) -> Token | None:
        """The @mention or /command being typed at the caret, if any."""
        before = self.text[: self.cursor]
        if before.startswith("/") and " " not in before and "\n" not in before:
            return Token("command", 0, self.cursor, before[1:])
        m = MENTION.search(before)
        if m:
            end = self.cursor
            while end < len(self.text) and not self.text[end].isspace():
                end += 1
            return Token("mention", m.start(), end, m.group(1))
        return None
