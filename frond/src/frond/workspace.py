"""The workspace: where frond works, what files exist there, and what the agent should know about it."""

from __future__ import annotations

import bisect
import datetime as dt
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path

SKIP_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".tox",
        ".nox",
        "dist",
        "build",
        "target",
        ".next",
        ".cache",
        ".idea",
        ".gradle",
        ".terraform",
        ".direnv",
        ".eggs",
        "site-packages",
    }
)
INSTRUCTION_FILES = ("AGENTS.md", "CLAUDE.md", "AGENT.md")
MAX_INDEX = 60_000
MAX_INSTRUCTION_CHARS = 12_000


@dataclass(frozen=True, slots=True)
class InstructionFile:
    path: str
    text: str


def _run(args: list[str], cwd: Path, timeout: float = 5.0) -> str | None:
    try:
        proc = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            timeout=timeout,
            check=False,
            stdin=subprocess.DEVNULL,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", errors="replace")


def find_git_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


class Workspace:
    """A root directory plus cached knowledge about it. Thread-safe for reads."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).expanduser().resolve()
        self.git_root = find_git_root(self.root)
        self._lock = threading.Lock()
        self._files: list[str] = []
        self._files_at = 0.0
        self._has_rg = shutil.which("rg") is not None

    # ── paths ────────────────────────────────────────────────────────────────

    def resolve(self, path: str | os.PathLike[str]) -> Path:
        p = Path(path).expanduser()
        if not p.is_absolute():
            p = self.root / p
        return Path(os.path.normpath(p))

    def rel(self, path: str | os.PathLike[str]) -> str:
        """A short display path: relative to the root when inside it, else absolute (with ~)."""
        p = self.resolve(path)
        try:
            return p.relative_to(self.root).as_posix() or "."
        except ValueError:
            home = Path.home()
            try:
                return "~/" + p.relative_to(home).as_posix()
            except ValueError:
                return p.as_posix()

    def is_inside(self, path: Path) -> bool:
        p = Path(os.path.realpath(path))
        roots = [self.root, Path(os.path.realpath(tempfile.gettempdir()))]
        return any(p == r or r in p.parents for r in roots)

    # ── file index ───────────────────────────────────────────────────────────

    def files(self, *, max_age: float = 3.0) -> list[str]:
        """Workspace-relative paths of files that are not ignored, sorted. Cached for ``max_age`` seconds."""
        with self._lock:
            if self._files and time.monotonic() - self._files_at < max_age:
                return self._files
        files = self._scan()
        with self._lock:
            self._files, self._files_at = files, time.monotonic()
        return files

    def invalidate(self) -> None:
        with self._lock:
            self._files_at = 0.0

    def _scan(self) -> list[str]:
        if self.git_root is not None:
            out = _run(
                ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--full-name"],
                self.root,
            )
            if out is not None:
                prefix = self.root.relative_to(self.git_root).as_posix() if self.root != self.git_root else ""
                paths = []
                for name in out.split("\0"):
                    if not name:
                        continue
                    if prefix:
                        if not name.startswith(prefix + "/"):
                            continue
                        name = name[len(prefix) + 1 :]
                    paths.append(name)
                paths = [p for p in dict.fromkeys(paths) if (self.root / p).exists()]
                return sorted(paths[:MAX_INDEX])
        if self._has_rg:
            out = _run(["rg", "--files", "--hidden", "--glob", "!.git"], self.root, timeout=10)
            if out is not None:
                return sorted(line for line in out.splitlines() if line)[:MAX_INDEX]
        return self._walk()

    def _walk(self) -> list[str]:
        found: list[str] = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".egg-info"))
            base = Path(dirpath).relative_to(self.root)
            for name in sorted(filenames):
                found.append((base / name).as_posix())
                if len(found) >= MAX_INDEX:
                    return found
        return found

    def directories(self) -> list[str]:
        files = self.files()
        cached = getattr(self, "_dirs", None)
        if cached is not None and cached[0] is files:
            return cached[1]
        dirs: set[str] = set()
        for f in files:
            parts = f.split("/")[:-1]
            for i in range(1, len(parts) + 1):
                dirs.add("/".join(parts[:i]) + "/")
        result = sorted(dirs)
        self._dirs = (files, result)
        return result

    def mention_index(self) -> FuzzyIndex:
        """A fuzzy index over files and folders, rebuilt only when the file list changes."""
        files = self.files()
        cached = getattr(self, "_mention_index", None)
        if cached is not None and cached[0] is files:
            return cached[1]
        index = FuzzyIndex(files + self.directories())
        self._mention_index = (files, index)
        return index

    # ── context for the agent ────────────────────────────────────────────────

    def instruction_files(self) -> list[InstructionFile]:
        """AGENTS.md-style files from the git root down to the workspace root, plus the user's global one."""
        found: list[InstructionFile] = []
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        global_file = config_home / "frond" / "AGENTS.md"
        if global_file.is_file():
            found.append(InstructionFile("~/.config/frond/AGENTS.md", _read_capped(global_file)))
        top = self.git_root or self.root
        chain = [self.root, *self.root.parents]
        chain = list(reversed(chain[: chain.index(top) + 1])) if top in chain else [self.root]
        for directory in chain:
            for name in INSTRUCTION_FILES:
                candidate = directory / name
                if candidate.is_file():
                    found.append(InstructionFile(self.rel(candidate), _read_capped(candidate)))
                    break  # one per directory: AGENTS.md wins over CLAUDE.md
        return found

    def git_summary(self) -> str | None:
        if self.git_root is None:
            return None
        status = _run(["git", "status", "--porcelain=v1", "--branch", "--untracked-files=normal"], self.root)
        if status is None:
            return None
        lines = status.splitlines()
        head = lines[0][3:] if lines and lines[0].startswith("## ") else "(unknown branch)"
        changes = lines[1:]
        out = [f"branch {head}", f"{len(changes)} uncommitted change(s)" if changes else "working tree clean"]
        out += [f"  {c}" for c in changes[:25]]
        if len(changes) > 25:
            out.append(f"  … {len(changes) - 25} more")
        log = _run(["git", "log", "-5", "--pretty=format:%h %s (%cr)"], self.root)
        if log:
            out.append("recent commits:")
            out += [f"  {line}" for line in log.splitlines()]
        return "\n".join(out)

    def tooling_hints(self) -> list[str]:
        r = self.root
        hints = []
        markers = [
            (
                "uv.lock",
                "uv project: run Python via `uv run ...` (e.g. `uv run pytest`), add deps with `uv add`",
            ),
            ("poetry.lock", "Poetry project: `poetry run ...`"),
            ("package-lock.json", "npm project (package-lock.json)"),
            ("pnpm-lock.yaml", "pnpm project"),
            ("yarn.lock", "yarn project"),
            ("bun.lock", "bun project"),
            ("Cargo.toml", "Rust/Cargo project: `cargo build`, `cargo test`"),
            ("go.mod", "Go module: `go build ./...`, `go test ./...`"),
            ("Makefile", "Makefile present: check its targets"),
            ("justfile", "justfile present: `just --list`"),
            ("pyproject.toml", "pyproject.toml present: read it for test/lint configuration"),
            ("tsconfig.json", "TypeScript project"),
        ]
        for name, hint in markers:
            if (r / name).exists():
                hints.append(hint)
        return hints

    def top_level(self, limit: int = 40) -> str:
        try:
            entries = sorted(self.root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            return "(unreadable)"
        names = [e.name + ("/" if e.is_dir() else "") for e in entries if e.name not in {".git", ".DS_Store"}]
        more = f", … {len(names) - limit} more" if len(names) > limit else ""
        return ", ".join(names[:limit]) + more

    def snapshot(self) -> str:
        """A compact text description of the environment, given to the agent at the start of every turn."""
        shell = os.environ.get("SHELL", "/bin/sh")
        lines = [
            f"cwd: {self.root}",
            f"platform: {platform.system()} {platform.release()} ({platform.machine()}), "
            f"shell {Path(shell).name}, Python {sys.version.split()[0]} (frond's own interpreter)",
            f"date: {dt.date.today().isoformat()}",
            f"top-level entries: {self.top_level()}",
            f"indexed files: {len(self.files())}",
            f"ripgrep: {'available' if self._has_rg else 'not installed (grep() falls back to Python)'}",
        ]
        git = self.git_summary()
        lines.append("git: " + git.replace("\n", "\n  ") if git else "git: not a git repository")
        hints = self.tooling_hints()
        if hints:
            lines.append("tooling:")
            lines += [f"  - {h}" for h in hints]
        instructions = self.instruction_files()
        if instructions:
            lines.append("")
            lines.append("Project instructions (follow them; deeper files take precedence):")
            for item in instructions:
                lines.append(f"--- {item.path} ---")
                lines.append(item.text.rstrip())
        return "\n".join(lines)


def _read_capped(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if len(text) > MAX_INSTRUCTION_CHARS:
        text = text[:MAX_INSTRUCTION_CHARS] + f"\n… (truncated; read {path} for the rest)"
    return text


# ── fuzzy matching (for @-mentions) ──────────────────────────────────────────

_BOUNDARY = frozenset("/_-. ")


def fuzzy_score(query: str, candidate: str) -> float | None:
    """Score how well ``query`` matches ``candidate`` as a subsequence. None means no match.

    The heuristics follow fzf's spirit: matches at word boundaries and consecutive runs score high,
    long gaps score low, and matches that land entirely in the basename win.
    """
    if not query:
        return 0.0
    q, c = query.lower(), candidate.lower()
    first: list[int] = []
    start = 0
    for ch in q:
        idx = c.find(ch, start)
        if idx < 0:
            return None
        first.append(idx)
        start = idx + 1
    # Walk back from the end of the first match to find the tightest window ending there.
    positions: list[int] = []
    qi, j = len(q) - 1, first[-1]
    while qi >= 0:
        if c[j] == q[qi]:
            positions.append(j)
            qi -= 1
        j -= 1
    positions.reverse()
    score = 0.0
    for k, p in enumerate(positions):
        score += 1.0
        if p == 0 or c[p - 1] in _BOUNDARY:
            score += 8.0
        elif candidate[p].isupper() and candidate[p - 1].islower():
            score += 6.0
        if k and p == positions[k - 1] + 1:
            score += 5.0
    span = positions[-1] - positions[0] + 1
    score -= (span - len(q)) * 0.6
    base_start = c.rstrip("/").rfind("/") + 1
    base = c[base_start:]
    if positions[0] >= base_start:
        score += 12.0
    if base.startswith(q):
        score += 18.0
    if base.rstrip("/") == q or base.rsplit(".", 1)[0] == q:
        score += 30.0
    score -= len(c) * 0.03
    return score


def fuzzy_rank(query: str, candidates: list[str], limit: int = 50) -> list[str]:
    return FuzzyIndex(candidates).rank(query, limit)


class FuzzyIndex:
    """Fuzzy search over a fixed list of paths, fast enough to run on every keystroke in a large repository.

    Basename-prefix matches are found with a cheap scan first; otherwise a compiled subsequence regex filters
    candidates before the (slower, Python-level) scoring, which only ever sees a bounded number of them.
    """

    MAX_SCORED = 3000

    def __init__(self, items: list[str]) -> None:
        self.items = items
        self.lower = [s.lower().replace("\n", " ") for s in items]
        self.base = [low.rstrip("/").rsplit("/", 1)[-1] for low in self.lower]
        self.blob = "\n".join(self.lower)
        self.offsets: list[int] = []
        self._last: tuple[str, list[int]] = ("", [])
        pos = 0
        for low in self.lower:
            self.offsets.append(pos)
            pos += len(low) + 1

    def rank(self, query: str, limit: int = 50) -> list[str]:
        if not query:
            return self.items[:limit]
        q = query.lower()
        items = self.items
        prefixed = [i for i, b in enumerate(self.base) if b.startswith(q)]
        if len(prefixed) >= limit:
            prefixed.sort(key=lambda i: (len(items[i]), items[i]))
            return [items[i] for i in prefixed[:limit]]
        # Possessive "[^c\\n]*+c" steps make the subsequence test linear (no backtracking).
        body = "".join(f"[^{re.escape(c)}\\n]*+{re.escape(c)}" for c in q)
        last_query, last_found = self._last
        if last_query and q.startswith(last_query) and len(last_found) < 20_000:
            step = re.compile(body)  # typing extends the query: only re-check what matched before
            found = [i for i in last_found if step.match(self.lower[i])]
        else:  # one C-level pass over every path
            pattern = re.compile("(?m)^" + body)
            found = [bisect.bisect_right(self.offsets, m.start()) - 1 for m in pattern.finditer(self.blob)]
        self._last = (q, found)
        if len(found) > self.MAX_SCORED:
            found.sort(key=lambda i: len(items[i]))
            found = found[: self.MAX_SCORED]
        scored = []
        for i in found:
            score = fuzzy_score(query, items[i])
            if score is not None:
                scored.append((score, items[i]))
        scored.sort(key=lambda t: (-t[0], len(t[1]), t[1]))
        return [c for _, c in scored[:limit]]
