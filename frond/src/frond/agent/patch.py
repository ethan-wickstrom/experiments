"""Parse and apply multi-file patches.

Two input formats are accepted because different models are fluent in different ones:

* the ``*** Begin Patch`` envelope used by OpenAI's Codex (``*** Add File``/``*** Update File``/
  ``*** Delete File``/``*** Move to``, ``@@`` context anchors), and
* ordinary unified diffs (``--- a/x`` / ``+++ b/x`` / ``@@ -1,3 +1,4 @@``).

Hunks are located by their content, so slightly stale diffs still apply. Matching falls back from exact to
trailing-whitespace-insensitive to fully whitespace-insensitive comparison; when a fallback matches, context lines
keep the file's own text (indentation, line endings), and only added lines come from the patch. Unified-diff line
numbers are used only to place pure insertions, which have no content to match.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal


class PatchError(ValueError):
    pass


@dataclass
class Chunk:
    anchor: str | None
    ops: list[tuple[str, str]] = field(default_factory=list)  # (" " | "-" | "+", text)
    eof: bool = False
    line_hint: int | None = None  # unified diffs: the old start line, used to place pure insertions

    @property
    def old(self) -> list[str]:
        return [text for op, text in self.ops if op != "+"]

    @property
    def new(self) -> list[str]:
        return [text for op, text in self.ops if op != "-"]


@dataclass
class FileOp:
    kind: Literal["add", "update", "delete"]
    path: str
    move_to: str | None = None
    content: str = ""
    chunks: list[Chunk] = field(default_factory=list)


def parse_patch(text: str) -> list[FileOp]:
    text = text.strip("\n")
    if "*** Begin Patch" in text:
        return _parse_envelope(text)
    if any(line.startswith("+++ ") for line in text.splitlines()):
        return _parse_unified(text)
    raise PatchError("unrecognized patch format: expected '*** Begin Patch' or a unified diff with ---/+++ headers")


def _parse_envelope(text: str) -> list[FileOp]:
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == "*** Begin Patch"), None)
    if start is None:
        raise PatchError("missing '*** Begin Patch'")
    end = next((i for i in range(len(lines) - 1, start, -1) if lines[i].strip() == "*** End Patch"), len(lines))
    ops: list[FileOp] = []
    i = start + 1
    while i < end:
        line = lines[i]
        if line.startswith("*** Add File: "):
            op = FileOp("add", line[len("*** Add File: ") :].strip())
            i += 1
            body = []
            while i < end and not lines[i].startswith("*** "):
                if not lines[i].startswith("+"):
                    raise PatchError(f"line {i + 1}: lines of an added file must start with '+': {lines[i]!r}")
                body.append(lines[i][1:])
                i += 1
            op.content = "\n".join(body) + ("\n" if body else "")
            ops.append(op)
        elif line.startswith("*** Delete File: "):
            ops.append(FileOp("delete", line[len("*** Delete File: ") :].strip()))
            i += 1
        elif line.startswith("*** Update File: "):
            op = FileOp("update", line[len("*** Update File: ") :].strip())
            i += 1
            if i < end and lines[i].startswith("*** Move to: "):
                op.move_to = lines[i][len("*** Move to: ") :].strip()
                i += 1
            chunk: Chunk | None = None
            while i < end and (not lines[i].startswith("*** ") or lines[i].strip() == "*** End of File"):
                cur = lines[i]
                if cur.strip() == "*** End of File":
                    if chunk is not None:
                        chunk.eof = True
                elif cur.startswith("@@"):
                    anchor = cur[2:].strip()
                    chunk = Chunk(anchor or None)
                    op.chunks.append(chunk)
                else:
                    if chunk is None:
                        chunk = Chunk(None)
                        op.chunks.append(chunk)
                    _add_line(chunk, cur)
                i += 1
            if not op.chunks and op.move_to is None:
                raise PatchError(f"update of {op.path} has no hunks")
            ops.append(op)
        elif not line.strip():
            i += 1
        else:
            raise PatchError(f"line {i + 1}: unexpected line {line!r}")
    if not ops:
        raise PatchError("patch contains no file operations")
    return ops


def _add_line(chunk: Chunk, line: str) -> None:
    if line.startswith(("+", "-", " ")):
        chunk.ops.append((line[0], line[1:]))
    elif line == "":
        chunk.ops.append((" ", ""))
    elif line.startswith("\\"):
        pass  # "\ No newline at end of file"
    else:
        raise PatchError(f"hunk line must start with ' ', '+' or '-': {line!r}")


def _strip_prefix(path: str) -> str:
    path = path.split("\t", 1)[0].strip()
    if path.startswith(("a/", "b/")):
        return path[2:]
    return path


def _parse_unified(text: str) -> list[FileOp]:
    lines = text.splitlines()
    ops: list[FileOp] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
            src = lines[i][4:].strip()
            dst = lines[i + 1][4:].strip()
            i += 2
            chunks: list[Chunk] = []
            chunk: Chunk | None = None
            while i < len(lines) and not (
                lines[i].startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ ")
            ):
                cur = lines[i]
                if cur.startswith("@@"):
                    header = _UNIFIED_HUNK.match(cur)
                    chunk = Chunk(None, line_hint=int(header.group(1)) if header else None)
                    chunks.append(chunk)
                elif chunk is not None and not cur.startswith(("diff --git", "index ", "new file", "deleted file")):
                    _add_line(chunk, cur)
                i += 1
            if src == "/dev/null":
                body = [line for c in chunks for line in c.new]
                ops.append(FileOp("add", _strip_prefix(dst), content="\n".join(body) + ("\n" if body else "")))
            elif dst == "/dev/null":
                ops.append(FileOp("delete", _strip_prefix(src)))
            else:
                op = FileOp("update", _strip_prefix(src), chunks=chunks)
                if _strip_prefix(dst) != _strip_prefix(src):
                    op.move_to = _strip_prefix(dst)
                ops.append(op)
        else:
            i += 1
    if not ops:
        raise PatchError("no file sections found in unified diff")
    return ops


_UNIFIED_HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@")
_NORMALIZERS: tuple[Callable[[str], str], ...] = (lambda s: s, str.rstrip, str.strip)


def _seek(lines: list[str], pattern: list[str], start: int, eof: bool) -> int | None:
    if not pattern:
        return start
    n = len(pattern)
    candidates = [len(lines) - n] if eof else []
    for norm in _NORMALIZERS:
        want = [norm(p) for p in pattern]
        for idx in candidates:
            if idx >= start and [norm(x) for x in lines[idx : idx + n]] == want:
                return idx
        for idx in range(start, len(lines) - n + 1):
            if [norm(x) for x in lines[idx : idx + n]] == want:
                return idx
    return None


def apply_chunks(original: str, chunks: list[Chunk], path: str) -> str:
    had_newline = original.endswith("\n")
    lines = original.split("\n")
    if had_newline:
        lines.pop()
    eol = "\r" if "\r\n" in original else ""  # added lines follow the file's line endings
    replacements: list[tuple[int, int, list[str]]] = []
    pos = 0
    for n, chunk in enumerate(chunks, 1):
        if chunk.anchor:
            idx = _seek(lines, [chunk.anchor], pos, False)
            if idx is None:
                raise PatchError(f"{path}: hunk {n}: anchor line not found: {chunk.anchor!r}")
            pos = idx + 1
        ops = chunk.ops
        old = [text for op, text in ops if op != "+"]
        if not old:
            if chunk.anchor:
                at = pos
            elif chunk.line_hint is not None:
                at = max(0, min(chunk.line_hint, len(lines)))  # "@@ -2,0 +3 @@" inserts after line 2
            else:
                at = len(lines)
            replacements.append((at, 0, [text + eol for op, text in ops if op == "+"]))
            pos = at
            continue
        idx = _seek(lines, old, pos, chunk.eof)
        if idx is None and ops and ops[-1] == (" ", ""):
            ops = ops[:-1]  # a trailing blank context line the file may not have at its end
            old = [text for op, text in ops if op != "+"]
            idx = _seek(lines, old, pos, chunk.eof) if old else pos
        if idx is None:
            preview = "\n".join(old[:8])
            raise PatchError(f"{path}: hunk {n}: could not find these lines (re-read the file and retry):\n{preview}")
        replacement: list[str] = []
        cursor = idx
        for op, text in ops:
            if op == " ":
                replacement.append(lines[cursor])  # the file's own text, not the patch's copy
                cursor += 1
            elif op == "-":
                cursor += 1
            else:
                replacement.append(text + eol)
        replacements.append((idx, len(old), replacement))
        pos = idx + len(old)
    for idx, length, new in sorted(replacements, key=lambda r: r[0], reverse=True):
        lines[idx : idx + length] = new
    out = "\n".join(lines)
    return out + "\n" if had_newline or not original else out
