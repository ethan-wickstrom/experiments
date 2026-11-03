"""The host-side tools the agent calls from its Python REPL.

Each public method of :class:`Toolbox` becomes a global function in the REPL. Docstrings are part of the
agent's prompt, so they are written for the model: what the tool does, what it returns, and when to use it.
Arguments and return values must be JSON-compatible because they cross a process boundary; dicts tagged
with ``__frond__`` are rehydrated into friendlier objects on the REPL side (see ``_worker.py``).
"""

from __future__ import annotations

import contextlib
import difflib
import inspect
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from frond.agent.diffing import make_diff
from frond.agent.freshness import Observation, Observations
from frond.agent.metrics import RunMetrics
from frond.agent.patch import FileOp, PatchError, apply_chunks, parse_patch
from frond.agent.policy import Policy
from frond.agent.shell import SANDBOX_UNAVAILABLE, JobManager, ShellRunner, sandbox_status, truncate_middle
from frond.agent.steplog import StepLog
from frond.agent.web import fetch_text
from frond.events import (
    ChangeKind,
    Emit,
    FileChanged,
    FileViewed,
    Notice,
    PlanItem,
    PlanStatus,
    PlanUpdated,
    SearchRan,
)
from frond.workspace import SKIP_DIRS, Workspace, fuzzy_rank
from frond.world import Timeline

VIEW_WINDOW = 300
MAX_LINE = 2000
MAX_READ_BYTES = 2_000_000
MAX_OUTPUT_CHARS = 24_000
MAX_COMMAND_DIFFS = 20  # diffs shown for files one shell command changed; undo covers the rest too
MAX_MATCH_TEXT = 400


class ToolError(Exception):
    """A tool failed in a way the model should read and recover from."""


@dataclass(frozen=True, slots=True)
class Delegate:
    """Runs a read-only sub-agent on a task. Provided by the session so tools stay free of LM wiring."""

    run: Callable[[str, str], str]
    run_many: Callable[[list[str]], list[str]]


def returns(description: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Document what a tool returns *inside the REPL* when that differs from its JSON wire type."""

    def mark(fn: Callable[..., Any]) -> Callable[..., Any]:
        setattr(fn, "_frond_returns", description)  # noqa: B010
        return fn

    return mark


def display_signature(fn: Callable[..., Any]) -> str:
    """A tool's signature as the model should see it: evaluated annotations, REPL-side return type."""
    target = getattr(fn, "__wrapped__", fn)
    try:
        sig = inspect.signature(target, eval_str=True)
    except Exception:
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            return "(...)"
    text = str(sig)
    override = getattr(fn, "_frond_returns", None) or getattr(target, "_frond_returns", None)
    if override:
        text = text.split(" -> ")[0] + f" -> {override}"
    return text


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Translate a gitignore-flavoured glob (``**``, ``*``, ``?``, ``[...]``, ``{a,b}``) to a regex."""
    i, out = 0, []
    while i < len(pattern):
        ch = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif ch == "*":
            out.append("[^/]*")
            i += 1
        elif ch == "?":
            out.append("[^/]")
            i += 1
        elif ch == "[":
            end = pattern.find("]", i + 1)
            if end == -1:
                out.append(re.escape(ch))
                i += 1
            else:
                body = pattern[i + 1 : end].replace("\\", "\\\\")
                if body.startswith("!"):
                    body = "^" + body[1:]
                out.append(f"[{body}]")
                i = end + 1
        elif ch == "{":
            end = pattern.find("}", i + 1)
            if end == -1:
                out.append(re.escape(ch))
                i += 1
            else:
                options = pattern[i + 1 : end].split(",")
                out.append("(?:" + "|".join(glob_to_regex(o).pattern[:-2] for o in options) + ")")
                i = end + 1
        else:
            out.append(re.escape(ch))
            i += 1
    return re.compile("".join(out) + r"\Z")


def _is_binary(sample: bytes) -> bool:
    return b"\0" in sample[:8192]


class Toolbox:
    """Tools bound to one workspace and one event stream. Sub-agents get a read-only toolbox."""

    MUTATING = frozenset({"write", "edit", "patch", "delete", "move"})

    def __init__(
        self,
        workspace: Workspace,
        emit: Emit,
        *,
        shell: ShellRunner,
        jobs: JobManager,
        policy: Policy,
        scope: str = "",
        read_only: bool = False,
        delegate: Delegate | None = None,
        memory: StepLog | None = None,
        timeline: Timeline | None = None,
        metrics: RunMetrics | None = None,
        observations: Observations | None = None,
        freshness: bool = True,
    ) -> None:
        self.ws = workspace
        self.memory = memory
        self.observations = observations  # what the model has read this turn (freshness, H3)
        self.freshness = freshness  # act on stale reads; off, they are only counted
        self.timeline = timeline  # snapshots around each command, to show what it changed (undo needs none of this)
        self.metrics = metrics  # counts every tool call and failure, for research (ledger B2)
        self.emit = emit
        self.shell = shell
        self._jobs = jobs
        self.policy = policy
        self.scope = scope
        self.read_only = read_only
        self.delegate = delegate
        self._write_lock = threading.Lock()

    def functions(self) -> list[Callable[..., Any]]:
        names = [
            "view",
            "read",
            "write",
            "edit",
            "patch",
            "delete",
            "move",
            "ls",
            "glob",
            "grep",
            "sh",
            "jobs",
            "job_output",
            "job_kill",
            "plan",
            "fetch",
        ]
        if self.memory is not None:
            names += ["history_search", "history_step"]
        if self.delegate is not None:
            names += ["subagent", "subagent_batched"]
        if self.read_only:
            names = [n for n in names if n not in self.MUTATING and n != "plan"]
        functions = [getattr(self, n) for n in names]
        return [self.metrics.counted(f) for f in functions] if self.metrics is not None else functions

    # ── helpers ──────────────────────────────────────────────────────────────

    def _path(self, path: str) -> Path:
        if not isinstance(path, str) or not path.strip():
            raise ToolError("path must be a non-empty string")
        return self.ws.resolve(path.strip())

    def _missing(self, path: str) -> FileNotFoundError:
        suggestions = fuzzy_rank(Path(path).name, self.ws.files(), limit=3)
        hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
        return FileNotFoundError(f"{path} does not exist.{hint}")

    def _read_text(self, p: Path, display: str, *, strict: bool = False, observe: bool = False) -> str:
        if not p.exists():
            raise self._missing(display)
        if p.is_dir():
            raise IsADirectoryError(f"{display} is a directory; use ls({display!r}) or view({display!r})")
        size = p.stat().st_size
        if size > MAX_READ_BYTES:
            raise ToolError(f"{display} is {size:,} bytes; use view() with a line range or grep() instead")
        data = p.read_bytes()
        if _is_binary(data):
            raise ToolError(f"{display} looks like a binary file ({size:,} bytes)")
        if observe and self.observations is not None:
            self.observations.saw(display, data)
        if strict:
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError:
                raise ToolError(f"{display} is not valid UTF-8; frond only edits UTF-8 text files") from None
        return data.decode("utf-8", errors="replace")

    def _check_write(self, p: Path) -> None:
        if self.read_only:
            raise PermissionError("this agent is read-only; report what should change instead")
        self.policy.check_write(p, self.ws.is_inside(p))

    def _stale(self, display: str, *, replaces: bool) -> Observation | None:
        """The model's read of ``display`` when the file changed since (counted as a stale action). With freshness
        on, an action that ``replaces`` the whole file is refused: it would overwrite a change the model never saw."""
        stale = self.observations.changed(display) if self.observations is not None else None
        if stale is None:
            return None
        if self.metrics is not None:
            self.metrics.bump("stale_actions")
        if self.freshness and replaces:
            raise ToolError(
                f"{display} changed since you read it at step {stale.step}. Read it again before replacing or "
                "deleting it, so the change made since is not lost."
            )
        return stale

    def _wrote(self, p: Path, display: str, stale: Observation | None) -> None:
        """After the model's own change the file holds what it intended, unless its picture was stale already."""
        if self.observations is not None and stale is None:
            with contextlib.suppress(OSError):
                self.observations.saw(display, (p.resolve() if p.is_symlink() else p).read_bytes())

    def _stale_note(self, display: str, stale: Observation | None) -> str:
        if stale is None or not self.freshness:
            return ""
        return (
            f". Note: {display} had changed since you read it at step {stale.step}; the edit applied where your "
            "old text still matched. Read the file again before relying on the rest of it."
        )

    def _commit(self, p: Path, display: str, old: str | None, new: str) -> tuple[int, int]:
        target = p.resolve() if p.is_symlink() else p
        target.parent.mkdir(parents=True, exist_ok=True)
        if old is not None and "\r\n" in old and "\r\n" not in new:
            new = new.replace("\n", "\r\n")
        tmp = target.with_name(f".{target.name}.frond-tmp")
        tmp.write_text(new, encoding="utf-8", newline="")
        if target.exists():
            shutil.copymode(target, tmp)
        os.replace(tmp, target)
        diff = make_diff(old or "", new, display, created=old is None)
        self.emit(
            FileChanged(
                display,
                "create" if old is None else "edit",
                diff.text,
                diff.added,
                diff.removed,
                scope=self.scope,
            )
        )
        self.ws.invalidate()
        return diff.added, diff.removed

    # ── reading ──────────────────────────────────────────────────────────────

    def view(self, path: str, start: int = 1, end: int | None = None) -> str:
        """Show a text file with line numbers (`  12│ code`), or list a directory.
        Without `end`, shows up to 300 lines from `start`. Read code with this before editing it."""
        p = self._path(path)
        display = self.ws.rel(p)
        if p.is_dir():
            return self.ls(path, depth=1)
        text = self._read_text(p, display, observe=True)
        lines = text.splitlines()
        total = len(lines)
        start = max(1, int(start))
        stop = min(total, int(end) if end is not None else start + VIEW_WINDOW - 1)
        if total == 0:
            self.emit(FileViewed(display, 0, 0, 0, self.scope))
            return f"{display} is empty"
        if start > total:
            raise ToolError(f"{display} has only {total} lines; start={start} is past the end")
        width = len(str(stop))
        out = []
        for n in range(start, stop + 1):
            line = lines[n - 1]
            if len(line) > MAX_LINE:
                line = line[:MAX_LINE] + f"… [{len(line) - MAX_LINE} more chars]"
            out.append(f"{n:>{width}}│ {line}")
        if stop < total:
            out.append(f"… {total - stop} more lines (view({display!r}, {stop + 1}) to continue; {total} total)")
        self.emit(FileViewed(display, start, stop, total, self.scope))
        return "\n".join(out)

    def read(self, path: str) -> str:
        """Return a file's full text, for processing in code (parsing, slicing, passing to llm_query).
        Use view() instead when you want to look at it."""
        p = self._path(path)
        display = self.ws.rel(p)
        text = self._read_text(p, display, observe=True)
        n = text.count("\n") + (0 if text.endswith("\n") or not text else 1)
        self.emit(FileViewed(display, 1, n, n, self.scope))
        return text

    def ls(self, path: str = ".", depth: int = 2) -> str:
        """List a directory as an indented tree, skipping ignored and generated files (.git, node_modules, …)."""
        root = self._path(path)
        if not root.exists():
            raise self._missing(path)
        if not root.is_dir():
            return self.ws.rel(root)
        depth = max(1, min(int(depth), 6))
        lines: list[str] = []
        limit = 400

        def walk(d: Path, level: int) -> None:
            try:
                entries = sorted(d.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
            except OSError as exc:
                lines.append("  " * level + f"(unreadable: {exc.strerror})")
                return
            for entry in entries:
                if len(lines) >= limit:
                    return
                if entry.name in SKIP_DIRS or entry.name in {".DS_Store"}:
                    continue
                if entry.is_dir():
                    if level + 1 < depth:
                        lines.append("  " * level + entry.name + "/")
                        walk(entry, level + 1)
                    else:
                        try:
                            count = sum(1 for _ in entry.iterdir())
                        except OSError:
                            count = 0
                        lines.append("  " * level + f"{entry.name}/  ({count} entries)")
                else:
                    lines.append("  " * level + entry.name)

        walk(root, 0)
        if len(lines) >= limit:
            lines.append(f"… (stopped at {limit} entries; ls a subdirectory for more)")
        self.emit(SearchRan("ls", self.ws.rel(root), len(lines), self.scope))
        return "\n".join(lines) if lines else "(empty directory)"

    def glob(self, pattern: str, path: str = ".") -> list[str]:
        """Find files by glob (`**/*.py`, `src/**/test_*.ts`, `*.{md,txt}`). A pattern without `/` matches
        file names at any depth. Ignored files are skipped. Returns workspace-relative paths."""
        base = self._path(path)
        base_rel = self.ws.rel(base)
        pattern = pattern[2:] if pattern.startswith("./") else pattern
        regex = glob_to_regex(pattern)
        name_only = "/" not in pattern
        out = []
        for f in self.ws.files():
            if base_rel not in (".", "") and not (f == base_rel or f.startswith(base_rel.rstrip("/") + "/")):
                continue
            rel = f if base_rel in (".", "") else f[len(base_rel.rstrip("/")) + 1 :]
            target = rel.rsplit("/", 1)[-1] if name_only else rel
            if regex.match(target):
                out.append(f)
        self.emit(SearchRan("glob", pattern, len(out), self.scope))
        return out[:2000]

    @returns("Matches")
    def grep(
        self,
        pattern: str,
        path: str = ".",
        glob: str | None = None,
        ignore_case: bool = False,
        context: int = 0,
        fixed: bool = False,
        max_results: int = 200,
    ) -> dict[str, Any]:
        """Search file contents with a regex (ripgrep syntax; `fixed=True` for a literal string).
        Returns a list-like of matches `m.path`, `m.line`, `m.text` (print it for a grouped view).
        `glob` narrows files (e.g. "*.py"); `context` adds surrounding lines."""
        base = self._path(path)
        if not base.exists():
            raise self._missing(path)
        max_results = max(1, min(int(max_results), 2000))
        context = max(0, min(int(context), 10))
        if shutil.which("rg"):
            items, truncated = self._grep_rg(pattern, base, glob, ignore_case, context, fixed, max_results)
        else:
            items, truncated = self._grep_py(pattern, base, glob, ignore_case, context, fixed, max_results)
        self.emit(SearchRan("grep", pattern, len(items), self.scope))
        files = len({m["path"] for m in items})
        return {
            "__frond__": "matches",
            "query": pattern,
            "items": items,
            "truncated": truncated,
            "files": files,
        }

    def _grep_rg(
        self,
        pattern: str,
        base: Path,
        glob: str | None,
        ignore_case: bool,
        context: int,
        fixed: bool,
        max_results: int,
    ) -> tuple[list[dict[str, Any]], bool]:
        args = ["rg", "--json", "--no-config", "--max-columns", "1000"]
        if ignore_case:
            args.append("-i")
        if fixed:
            args.append("-F")
        if context:
            args += ["-C", str(context)]
        if glob:
            args += ["--glob", glob]
        args += ["-e", pattern, "--", str(base)]
        timed_out = threading.Event()
        # ripgrep's output is read as it streams and the search is stopped at the limit: a broad pattern in a
        # large repository prints far more than was asked for. stderr goes to a file so it cannot fill a pipe.
        with tempfile.TemporaryFile() as errors:
            proc = subprocess.Popen(
                args, cwd=self.ws.root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=errors
            )

            def expire() -> None:
                timed_out.set()
                proc.kill()

            timer = threading.Timer(60, expire)
            timer.start()
            try:
                items, truncated, saw_output = self._read_rg(proc, context, max_results)
            finally:
                timer.cancel()
                if proc.poll() is None:
                    proc.kill()
                if proc.stdout is not None:
                    proc.stdout.close()
                proc.wait()
            if timed_out.is_set():
                raise ToolError("grep timed out after 60s; narrow the path or glob")
            if proc.returncode == 2 and not saw_output:
                errors.seek(0)
                raise ToolError(errors.read().decode(errors="replace").strip() or "ripgrep failed")
        return items, truncated

    def _read_rg(
        self, proc: subprocess.Popen[bytes], context: int, max_results: int
    ) -> tuple[list[dict[str, Any]], bool, bool]:
        """Collect matches from ripgrep's JSON stream. Returns (matches, stopped at the limit, any output)."""
        items: list[dict[str, Any]] = []
        pending_before: list[list[Any]] = []
        saw_output = False
        assert proc.stdout is not None
        for raw in proc.stdout:
            saw_output = True
            try:
                msg = json.loads(raw)
            except ValueError:
                break  # a line cut short because the search was stopped
            kind = msg.get("type")
            if kind not in {"match", "context"}:
                if kind == "end":
                    pending_before = []
                continue
            data = msg["data"]
            text = data["lines"].get("text", "").rstrip("\n")[:MAX_MATCH_TEXT]
            rel = self.ws.rel(data["path"]["text"])
            line = data["line_number"]
            if kind == "match":
                if len(items) >= max_results:
                    return items, True, saw_output
                items.append({"path": rel, "line": line, "text": text, "before": pending_before, "after": []})
                pending_before = []
            elif (
                items
                and items[-1]["path"] == rel
                and line > items[-1]["line"]
                and line - items[-1]["line"] <= context
                and not pending_before
            ):
                items[-1]["after"].append([line, text])
            else:
                pending_before = [*pending_before, [line, text]][-context:] if context else []
        return items, False, saw_output

    def _grep_py(
        self,
        pattern: str,
        base: Path,
        glob: str | None,
        ignore_case: bool,
        context: int,
        fixed: bool,
        max_results: int,
    ) -> tuple[list[dict[str, Any]], bool]:
        flags = re.IGNORECASE if ignore_case else 0
        try:
            regex = re.compile(re.escape(pattern) if fixed else pattern, flags)
        except re.error as exc:
            raise ToolError(f"invalid regex: {exc}") from None
        glob_re = glob_to_regex(glob) if glob else None
        base_rel = self.ws.rel(base)
        candidates = (
            [base_rel]
            if base.is_file()
            else [f for f in self.ws.files() if base_rel in (".", "") or f.startswith(base_rel.rstrip("/") + "/")]
        )
        items: list[dict[str, Any]] = []
        for rel in candidates:
            if glob_re and not glob_re.match(rel if "/" in (glob or "") else rel.rsplit("/", 1)[-1]):
                continue
            p = self.ws.root / rel
            try:
                if p.stat().st_size > MAX_READ_BYTES:
                    continue
                data = p.read_bytes()
            except OSError:
                continue
            if _is_binary(data):
                continue
            lines = data.decode("utf-8", errors="replace").splitlines()
            for idx, line in enumerate(lines):
                if regex.search(line):
                    if len(items) >= max_results:
                        return items, True
                    before = [[j + 1, lines[j][:MAX_MATCH_TEXT]] for j in range(max(0, idx - context), idx)]
                    after = [
                        [j + 1, lines[j][:MAX_MATCH_TEXT]] for j in range(idx + 1, min(len(lines), idx + 1 + context))
                    ]
                    items.append(
                        {
                            "path": rel,
                            "line": idx + 1,
                            "text": line[:MAX_MATCH_TEXT],
                            "before": before,
                            "after": after,
                        }
                    )
        return items, False

    # ── writing ──────────────────────────────────────────────────────────────

    def write(self, path: str, content: str) -> str:
        """Create a new file, or replace a file's entire content. Parent directories are created.
        The user sees the diff. Prefer edit() for changing part of an existing file."""
        p = self._path(path)
        display = self.ws.rel(p)
        if p.is_dir():
            raise IsADirectoryError(f"{display} is a directory")
        self._check_write(p)
        if not isinstance(content, str):
            raise ToolError("content must be a string")
        with self._write_lock:
            old = self._read_text(p, display, strict=True) if p.exists() else None
            if old == content:
                return f"{display} unchanged (content identical)"
            stale = self._stale(display, replaces=True)
            added, removed = self._commit(p, display, old, content)
            self._wrote(p, display, stale)
        lines = content.count("\n") + (0 if content.endswith("\n") or not content else 1)
        if old is None:
            return f"created {display} ({lines} lines)"
        return f"rewrote {display} (+{added} −{removed}, now {lines} lines)"

    def edit(self, path: str, old: str, new: str, replace_all: bool = False) -> str:
        """Replace an exact snippet of a file. `old` must match the file text exactly (whitespace included)
        and be unique unless `replace_all=True`; include enough surrounding lines to make it unique.
        With `old=""` on a missing file, creates it with `new`. The user sees the diff."""
        p = self._path(path)
        display = self.ws.rel(p)
        self._check_write(p)
        if not p.exists():
            if old == "":
                return self.write(path, new)
            raise self._missing(display)
        if old == new:
            raise ToolError("old and new are identical; nothing to change")
        if old == "":
            raise ToolError("old is empty; to replace the whole file use write(), to create a file pass a new path")
        with self._write_lock:
            text = self._read_text(p, display, strict=True)
            updated = self._replace(text, old, new, replace_all, display)
            stale = self._stale(display, replaces=False)
            added, removed = self._commit(p, display, text, updated)
            self._wrote(p, display, stale)
        prefix = next(
            (i for i, (a, b) in enumerate(zip(text, updated, strict=False)) if a != b), min(len(text), len(updated))
        )
        line = text.count("\n", 0, prefix) + 1
        return f"edited {display} at line {line} (+{added} −{removed}){self._stale_note(display, stale)}"

    @staticmethod
    def _replace(text: str, old: str, new: str, replace_all: bool, display: str) -> str:
        crlf = "\r\n" in text
        if crlf and "\r\n" not in old:
            old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
        count = text.count(old)
        if count == 1 or (count > 1 and replace_all):
            return text.replace(old, new)
        if count > 1:
            lines = []
            pos = text.find(old)
            while pos >= 0:
                lines.append(str(text.count("\n", 0, pos) + 1))
                pos = text.find(old, pos + 1)
            raise ToolError(
                f"`old` occurs {count} times in {display} (at lines {', '.join(lines)}). "
                "Add surrounding lines to make it unique, or pass replace_all=True."
            )
        # No exact match: tolerate trailing-whitespace drift, a common transcription error.
        nl = "\r\n" if crlf else "\n"
        file_lines = text.split(nl)
        old_lines = old.split(nl)
        if old_lines and old_lines[-1] == "":
            old_lines = old_lines[:-1]
        want = [line.rstrip() for line in old_lines]
        hits = [
            i
            for i in range(len(file_lines) - len(want) + 1)
            if [line.rstrip() for line in file_lines[i : i + len(want)]] == want
        ]
        if len(hits) == 1:
            i = hits[0]
            new_body = new[: -len(nl)] if new.endswith(nl) else new
            new_lines = new_body.split(nl) if new_body else []
            return nl.join(file_lines[:i] + new_lines + file_lines[i + len(want) :])
        # Point the model at the closest region so its next attempt can succeed.
        probe = next((line for line in old_lines if line.strip()), "")
        close = difflib.get_close_matches(probe, file_lines, n=1, cutoff=0.5)
        hint = ""
        if close:
            idx = file_lines.index(close[0])
            lo, hi = max(0, idx - 3), min(len(file_lines), idx + 4)
            snippet = "\n".join(f"{n + 1:>5}│ {file_lines[n]}" for n in range(lo, hi))
            hint = f"\nClosest match near line {idx + 1}:\n{snippet}"
        raise ToolError(
            f"`old` was not found in {display}. Re-read the file with view() and copy the text exactly.{hint}"
        )

    def patch(self, patch: str) -> str:
        """Apply a multi-file patch: either the `*** Begin Patch` format (*** Add File / *** Update File /
        *** Delete File / *** Move to, with @@ hunks of ' ', '-', '+' lines) or a unified diff.
        Hunks are matched by content, not line numbers. All files are validated before any is written."""
        try:
            ops = parse_patch(patch)
        except PatchError as exc:
            raise ToolError(str(exc)) from None
        planned: list[tuple[FileOp, Path, str | None, str | None]] = []  # op, path, old, new
        touched: set[Path] = set()
        stale: dict[Path, Observation | None] = {}  # checked while planning, so a refusal writes nothing

        def claim(path: Path) -> None:
            if path in touched:
                raise ToolError(f"{self.ws.rel(path)} appears more than once in this patch; combine its hunks")
            touched.add(path)

        with self._write_lock:
            for op in ops:
                p = self._path(op.path)
                display = self.ws.rel(p)
                self._check_write(p)
                claim(p)
                if op.kind == "add":
                    if p.exists():
                        raise ToolError(f"*** Add File: {display} already exists; use *** Update File")
                    planned.append((op, p, None, op.content))
                elif op.kind == "delete":
                    planned.append((op, p, self._read_text(p, display, strict=True), None))
                    stale[p] = self._stale(display, replaces=True)
                else:
                    old = self._read_text(p, display, strict=True)
                    stale[p] = self._stale(display, replaces=False)
                    try:
                        new = apply_chunks(old, op.chunks, display) if op.chunks else old
                    except PatchError as exc:
                        raise ToolError(str(exc)) from None
                    if op.move_to:
                        dest = self._path(op.move_to)
                        if dest.exists() and dest != p:
                            raise ToolError(f"*** Move to: {self.ws.rel(dest)} already exists")
                        self._check_write(dest)
                        claim(dest)
                    planned.append((op, p, old, new))
            summary = []
            for op, p, old, new in planned:
                display = self.ws.rel(p)
                if op.kind == "delete":
                    p.unlink()
                    diff = make_diff(old or "", "", display, deleted=True)
                    self.emit(FileChanged(display, "delete", diff.text, 0, diff.removed, scope=self.scope))
                    summary.append(f"deleted {display}")
                    continue
                assert new is not None
                note = self._stale_note(display, stale.get(p))
                if op.move_to:
                    dest = self._path(op.move_to)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(p, dest)
                    added, removed = self._commit(dest, self.ws.rel(dest), old, new)
                    self._wrote(dest, self.ws.rel(dest), stale.get(p))
                    summary.append(f"moved {display} → {self.ws.rel(dest)} (+{added} −{removed}){note}")
                else:
                    added, removed = self._commit(p, display, old, new)
                    self._wrote(p, display, stale.get(p))
                    summary.append(f"{'created' if old is None else 'updated'} {display} (+{added} −{removed}){note}")
            self.ws.invalidate()
        return "\n".join(summary)

    def delete(self, path: str, recursive: bool = False) -> str:
        """Delete a file (or a directory with recursive=True). The user sees what was removed."""
        p = self._path(path)
        display = self.ws.rel(p)
        if not p.exists() and not p.is_symlink():
            raise self._missing(display)
        self._check_write(p)
        if p.is_symlink():  # remove the link itself, never what it points to
            target = os.readlink(p)
            p.unlink()
            self.emit(FileChanged(display, "delete", f"(symbolic link to {target})", 0, 0, scope=self.scope))
            self.ws.invalidate()
            return f"deleted symbolic link {display} (it pointed to {target})"
        if p.is_dir():
            if not recursive:
                raise ToolError(f"{display} is a directory; pass recursive=True to delete it and its contents")
            count = sum(1 for _ in p.rglob("*"))
            if count:
                self.policy.check_delete_tree(p, f"{display}/ ({count} {'entry' if count == 1 else 'entries'})")
            shutil.rmtree(p)
            self.emit(FileChanged(display + "/", "delete", f"(directory with {count} entries)", 0, 0, scope=self.scope))
            self.ws.invalidate()
            return f"deleted directory {display} ({count} entries)"
        try:
            old = self._read_text(p, display)
        except ToolError:
            old = ""
        self._stale(display, replaces=True)
        p.unlink()
        diff = make_diff(old, "", display, deleted=True)
        self.emit(FileChanged(display, "delete", diff.text, 0, diff.removed, scope=self.scope))
        self.ws.invalidate()
        return f"deleted {display}"

    def move(self, src: str, dst: str) -> str:
        """Move or rename a file or directory. Parent directories of `dst` are created."""
        s, d = self._path(src), self._path(dst)
        if not s.exists():
            raise self._missing(src)
        if d.exists():
            raise FileExistsError(f"{self.ws.rel(d)} already exists")
        self._check_write(s)
        self._check_write(d)
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(s), str(d))
        self.emit(FileChanged(self.ws.rel(d), "move", "", 0, 0, old_path=self.ws.rel(s), scope=self.scope))
        self.ws.invalidate()
        return f"moved {self.ws.rel(s)} → {self.ws.rel(d)}"

    # ── running things ───────────────────────────────────────────────────────

    @returns("CommandResult")
    def sh(
        self, command: str, timeout: float = 120, background: bool = False, cwd: str | None = None
    ) -> dict[str, Any]:
        """Run a shell command (bash) in the workspace; stdin is closed, output is stdout+stderr combined.
        Returns `r.ok`, `r.exit_code`, `r.output`, `r.log` (full output file). Use background=True for servers
        and watchers; it returns `r.job` for job_output()/job_kill(). The user sees every command."""
        if not isinstance(command, str) or not command.strip():
            raise ToolError("command must be a non-empty string")
        workdir = self._path(cwd) if cwd else self.ws.root
        if not workdir.is_dir():
            raise NotADirectoryError(f"cwd {cwd!r} is not a directory")
        if self.read_only or self.policy.mode == "readonly":
            return self._sh_sandboxed(command, workdir, timeout, background)
        self.policy.check_command(command)
        if background:
            job = self._jobs.start(command, workdir, self.shell.env(), scope=self.scope)
            deadline = time.monotonic() + 1.5
            while time.monotonic() < deadline and job.proc.poll() is None:
                time.sleep(0.1)
            initial = self._jobs.output(job.job_id, tail=40)
            return {
                "__frond__": "job",
                "job": job.job_id,
                "pid": job.proc.pid,
                "running": job.proc.poll() is None,
                "exit_code": job.proc.poll(),
                "output": initial,
                "log": str(job.log_path),
                "command": command,
            }
        timeout = max(1.0, min(float(timeout), 3600.0))
        timeline = self.timeline if self.timeline is not None and self.timeline.command_diffs else None
        before = timeline.snapshot() if timeline is not None else ""
        result = self.shell.run(command, cwd=workdir, timeout=timeout, scope=self.scope)
        self.ws.invalidate()
        if timeline is not None and before:
            self._show_command_changes(timeline, before, timeline.snapshot(new_ignored=True))
        output = truncate_middle(
            result.output,
            MAX_OUTPUT_CHARS,
            note=f"; the full output is in {result.log_path}: grep it, or view a range of it",
        )
        return {
            "__frond__": "command",
            "command": command,
            "exit_code": result.exit_code,
            "status": result.status,
            "ok": result.ok,
            "output": output,
            "duration": round(result.duration, 2),
            "log": result.log_path,
            "truncated": result.total_chars > MAX_OUTPUT_CHARS,
        }

    def _show_command_changes(self, timeline: Timeline, before: str, after: str) -> None:
        """Show the diffs of what a command changed, from the worlds before and after it (frond.world)."""
        changes = timeline.diff(before, after)
        shown = 0
        for change in changes:
            if shown == MAX_COMMAND_DIFFS:
                break
            if any(e is not None and e.kind != "file" for e in (change.before, change.after)):
                continue  # links and directories: undo covers them; there is no text to show
            old, new = timeline.content(change.before) or b"", timeline.content(change.after) or b""
            if b"\0" in old or b"\0" in new:
                continue
            kind: ChangeKind = "create" if change.before is None else "delete" if change.after is None else "edit"
            text_old, text_new = old.decode("utf-8", errors="replace"), new.decode("utf-8", errors="replace")
            diff = make_diff(text_old, text_new, change.path, created=kind == "create", deleted=kind == "delete")
            self.emit(FileChanged(change.path, kind, diff.text, diff.added, diff.removed, scope=self.scope))
            shown += 1
        if len(changes) > shown:
            self.emit(Notice("info", f"the command changed {len(changes)} paths; /undo covers all of them"))

    def _sh_sandboxed(self, command: str, workdir: Path, timeout: float, background: bool) -> dict[str, Any]:
        """A read-only agent's command, in an OS sandbox that refuses every filesystem write (see _sandbox.py).

        Nothing it runs can change files, so it needs no approval; without a sandbox it does not run at all."""
        if background:
            raise PermissionError("a read-only agent cannot start background jobs; report what should run instead")
        available, why = sandbox_status(self.ws.root)
        if not available:
            raise PermissionError(
                f"read-only commands run only inside an OS sandbox, and none is available here ({why}). "
                "Use view(), grep(), glob() and ls() instead, or report the command for the main agent to run."
            )
        timeout = max(1.0, min(float(timeout), 3600.0))
        result = self.shell.run(command, cwd=workdir, timeout=timeout, scope=self.scope, sandboxed=True)
        if result.exit_code == SANDBOX_UNAVAILABLE and result.output.startswith("frond-sandbox:"):
            raise PermissionError(result.output.strip())
        output = truncate_middle(
            result.output,
            MAX_OUTPUT_CHARS,
            note=f"; the full output is in {result.log_path}: grep it, or view a range of it",
        )
        return {
            "__frond__": "command",
            "command": command,
            "exit_code": result.exit_code,
            "status": result.status,
            "ok": result.ok,
            "output": output,
            "duration": round(result.duration, 2),
            "log": result.log_path,
            "truncated": result.total_chars > MAX_OUTPUT_CHARS,
            "sandbox": why,
        }

    def jobs(self) -> list[dict[str, Any]]:
        """List background jobs started with sh(..., background=True)."""
        return [
            {
                "job": j.job_id,
                "command": j.command,
                "pid": j.pid,
                "running": j.running,
                "exit_code": j.exit_code,
            }
            for j in (job.info() for job in self._jobs.snapshot())
        ]

    def job_output(self, job: int, tail: int = 100) -> str:
        """The last `tail` lines of a background job's output (tail=0 for all of it)."""
        try:
            return self._jobs.output(int(job), int(tail))
        except KeyError as exc:
            raise ToolError(str(exc.args[0])) from None

    def job_kill(self, job: int) -> str:
        """Stop a background job and everything it started."""
        try:
            code = self._jobs.kill(int(job))
        except KeyError as exc:
            raise ToolError(str(exc.args[0])) from None
        return f"job {job} stopped (exit code {code})"

    # ── the conversation's record ────────────────────────────────────────────

    def history_search(self, query: str, k: int = 8) -> list[dict[str, Any]]:
        """Search everything earlier in this conversation, in every turn: the user's messages, your answers, and
        each REPL step's reasoning, code and full output, including steps folded out of the prompt. Matches words
        and identifiers (BM25), best first. Each hit: seq (pass it to history_step), kind ("user", "step" or
        "answer"), turn, step, headline, and the best matching line."""
        if self.memory is None:
            raise ToolError("there is no conversation record in this session")
        return self.memory.search(str(query), max(1, min(int(k), 50)))

    def history_step(self, seq: int) -> dict[str, Any]:
        """One record of the conversation exactly as it was, by seq: a user message, an answer, or a step with
        its reasoning, code and full output."""
        if self.memory is None:
            raise ToolError("there is no conversation record in this session")
        record = self.memory.get(int(seq))
        if record is None:
            raise ToolError(f"no record {seq}; seq runs from 1 to {self.memory.last_seq}")
        return record.public()

    # ── planning, web, delegation ────────────────────────────────────────────

    def plan(self, steps: list[str]) -> str:
        """Show the user a checklist for multi-step work and keep it current as you go. Prefix each step:
        "[x] " done, "[>] " in progress, "[ ] " to do. Skip it for small tasks."""
        if not isinstance(steps, list) or not steps:
            raise ToolError("steps must be a non-empty list of strings")
        prefixes: tuple[tuple[str, PlanStatus], ...] = (
            ("[x]", "done"),
            ("[X]", "done"),
            ("[>]", "active"),
            ("[~]", "active"),
            ("[ ]", "todo"),
        )
        items: list[PlanItem] = []
        for raw in steps:
            text = str(raw).strip()
            status: PlanStatus = "todo"
            for prefix, st in prefixes:
                if text.startswith(prefix):
                    status, text = st, text[len(prefix) :].strip()
                    break
            items.append(PlanItem(text, status))
        self.emit(PlanUpdated(tuple(items)))
        done = sum(1 for i in items if i.status == "done")
        return f"plan updated ({done}/{len(items)} done)"

    def fetch(self, url: str, max_chars: int = 20000) -> str:
        """Fetch a web page (docs, changelogs, issues) as plain text, truncated to `max_chars`."""
        _ctype, text = fetch_text(url)
        self.emit(SearchRan("fetch", url, len(text), self.scope))
        return truncate_middle(text, max(1000, int(max_chars)))

    def subagent(self, task: str, context: str = "") -> str:
        """Delegate a self-contained, read-only investigation (e.g. "find every caller of X and how each uses
        it") to a sub-agent with a fresh context and the same read/search/sh tools. Returns its report.
        Use it to keep large explorations out of your own context."""
        if self.delegate is None:
            raise ToolError("sub-agents are not available here")
        return self.delegate.run(task, context)

    def subagent_batched(self, tasks: list[str]) -> list[str]:
        """Run several independent sub-agent investigations concurrently; returns their reports in order."""
        if self.delegate is None:
            raise ToolError("sub-agents are not available here")
        return self.delegate.run_many([str(t) for t in tasks])
