"""Worlds: workspace states as immutable, content-addressed values (decision D22, design.md "Architecture: worlds").

A snapshot of a directory is a tree id. Objects are named by their content, BLAKE2b-256 over a type tag and the
bytes, and stored once (zlib). Trees are nested and Merkle-hashed like git's, so two snapshots share every directory
that did not change, and diffing them descends only into subtrees whose ids differ: the cost follows the change, not
the size of the workspace.

Everything here is the standard library; git is not needed, so worlds work in any directory, including the minimal
containers benchmarks run in.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import shutil
import stat
import tempfile
import time
import zlib
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

# Never part of a world: version-control metadata, frond's own state, and caches that are rebuilt, not edited.
EXCLUDED = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".frond",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".venv",
        "node_modules",
    }
)
MAX_BLOB = 64 * 1024 * 1024  # larger files are tracked by a stat signature: changes are seen, contents not kept


class TooLarge(Exception):
    """The directory holds more files than a snapshot may visit (``Worktree.max_files``)."""


RACY_NS = 2_000_000_000  # a file modified this close to a snapshot is re-hashed even if its stat is unchanged


@dataclass(frozen=True, slots=True)
class Entry:
    """One name in a tree."""

    kind: str  # "file", "link" (the blob is the target), "tree", or "large" (a stat signature, no content)
    oid: str
    mode: int = 0  # permission bits, for files


@dataclass(frozen=True, slots=True)
class Change:
    """A path whose entry differs between two trees (None: absent). Trees are expanded to the paths inside."""

    path: str
    before: Entry | None
    after: Entry | None


def object_id(kind: str, data: bytes) -> str:
    return hashlib.blake2b(kind.encode() + b"\0" + data, digest_size=32).hexdigest()


class Store:
    """Immutable objects on disk, by id."""

    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(mode=0o700, parents=True, exist_ok=True)  # it holds the workspace's contents: private
        (root / "objects").mkdir(mode=0o700, exist_ok=True)

    def _path(self, oid: str) -> Path:
        return self.root / "objects" / oid[:2] / oid[2:]

    def put(self, kind: str, data: bytes) -> str:
        oid = object_id(kind, data)
        path = self._path(oid)
        try:
            os.utime(path)  # stored already: mark it in use, so a sweep never takes it from a tree being built
        except FileNotFoundError:
            path.parent.mkdir(exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
            with os.fdopen(fd, "wb") as f:
                f.write(zlib.compress(kind.encode() + b"\0" + data, 1))
            os.replace(tmp, path)
        return oid

    # ── garbage collection (ledger G21) ──────────────────────────────────────

    def size(self) -> int:
        """Bytes the objects take on disk."""
        return sum(f.stat().st_size for f in (self.root / "objects").glob("*/*"))

    def reachable(self, roots: Iterable[str]) -> set[str]:
        """Every object reachable from the given tree ids (missing or malformed ones are skipped)."""
        seen: set[str] = set()
        stack = [r for r in roots if r]
        while stack:
            oid = stack.pop()
            if oid in seen:
                continue
            seen.add(oid)
            try:
                entries = self.tree(oid)
            except (OSError, ValueError, zlib.error):
                continue
            for entry in entries.values():
                if entry.kind == "tree":
                    stack.append(entry.oid)
                elif entry.kind in ("file", "link"):
                    seen.add(entry.oid)
        return seen

    def sweep(self, keep: set[str], *, older_than: float) -> int:
        """Delete the objects outside ``keep`` last used before ``older_than`` (a timestamp); bytes freed.

        Each candidate is first renamed aside, so a ``put`` from then on writes the object anew rather than marking
        the one about to go; it is deleted only if, once aside, it still shows no use. A ``put`` that marked it in
        between, for a tree being built, brings it back (F45). Leftovers of an interrupted sweep are put back first.
        """
        freed = 0
        for directory in (self.root / "objects").iterdir():
            if not directory.is_dir():
                continue
            for aside in directory.glob(".gone-*"):
                _restore(aside)
            for path in directory.iterdir():
                if path.name.startswith((".tmp-", ".gone-")) or directory.name + path.name in keep:
                    continue
                try:
                    if path.stat().st_mtime >= older_than:
                        continue
                    aside = path.with_name(f".gone-{path.name}")
                    os.rename(path, aside)
                    st = aside.stat()
                    if st.st_mtime >= older_than:  # put marked it before the rename: in use again
                        _restore(aside)
                        continue
                    aside.unlink()
                    freed += st.st_size
                except FileNotFoundError:
                    continue
        return freed

    def get(self, oid: str) -> tuple[str, bytes]:
        kind, _, data = zlib.decompress(self._path(oid).read_bytes()).partition(b"\0")
        return kind.decode(), data

    def blob(self, oid: str) -> bytes:
        kind, data = self.get(oid)
        if kind != "blob":
            raise ValueError(f"{oid} is a {kind}, not a blob")
        return data

    def put_tree(self, entries: dict[str, Entry]) -> str:
        rows = [[name, e.kind, e.oid, e.mode] for name, e in sorted(entries.items())]
        return self.put("tree", json.dumps(rows, separators=(",", ":")).encode())

    def tree(self, oid: str) -> dict[str, Entry]:
        kind, data = self.get(oid)
        if kind != "tree":
            raise ValueError(f"{oid} is a {kind}, not a tree")
        return {name: Entry(k, o, m) for name, k, o, m in json.loads(data)}

    def files(self, oid: str, prefix: str = "") -> Iterator[tuple[str, Entry]]:
        """Every leaf under a tree: files, links, large files, and empty directories (as empty trees)."""
        entries = self.tree(oid)
        if not entries and prefix:
            yield prefix.rstrip("/"), Entry("tree", oid)
        for name, entry in entries.items():
            if entry.kind == "tree":
                yield from self.files(entry.oid, f"{prefix}{name}/")
            else:
                yield f"{prefix}{name}", entry

    def diff(self, a: str | None, b: str | None, prefix: str = "") -> list[Change]:
        """Leaf-level changes from tree ``a`` to tree ``b``, descending only where subtree ids differ."""
        if a == b:
            return []
        left = self.tree(a) if a else {}
        right = self.tree(b) if b else {}
        out: list[Change] = []
        for name in sorted(left.keys() | right.keys()):
            ea, eb = left.get(name), right.get(name)
            if ea == eb:
                continue
            path = f"{prefix}{name}"
            if ea is not None and eb is not None and ea.kind == eb.kind == "tree":
                out.extend(self.diff(ea.oid, eb.oid, f"{path}/"))
                if not self.tree(eb.oid):  # emptied: the directory itself stays, after its contents go
                    out.append(Change(path, None, eb))
                continue
            if ea is not None and ea.kind == "tree":
                out.extend(Change(p, e, None) for p, e in self._leaves(ea.oid, path))
                ea = None
            if eb is not None and eb.kind == "tree":
                out.extend(Change(p, None, e) for p, e in self._leaves(eb.oid, path))
                eb = None
            if ea is not None or eb is not None:
                out.append(Change(path, ea, eb))
        return out

    def _leaves(self, oid: str, path: str) -> list[tuple[str, Entry]]:
        leaves = list(self.files(oid, f"{path}/"))
        return leaves or [(path, Entry("tree", oid))]  # an empty directory is a leaf of its own


def _restore(aside: Path) -> None:
    """Put an object set aside by a sweep back under its name, unless a ``put`` wrote it there anew meanwhile: that copy
    stays, with its newer time, and the aside goes (review of #25)."""
    target = aside.with_name(aside.name.removeprefix(".gone-"))
    try:
        os.link(aside, target)  # never replaces an existing file
    except FileExistsError:
        pass
    except OSError:  # no hard links here: the check and the rename are not one step, but nearly
        if not target.exists():
            with contextlib.suppress(OSError):
                os.rename(aside, target)
    with contextlib.suppress(OSError):
        aside.unlink()


class Worktree:
    """A directory and the snapshots taken of it, with a stat cache so only changed files are read again."""

    def __init__(
        self,
        store: Store,
        root: Path,
        *,
        exclude: frozenset[str] = EXCLUDED,
        max_blob: int = MAX_BLOB,
        max_files: int | None = None,
    ):
        self.store = store
        self.root = root
        self.exclude = exclude
        self.max_blob = max_blob
        self.max_files = max_files  # past this many files a snapshot raises TooLarge (frond started in $HOME, say)
        self._visited = 0
        self.ignored: frozenset[str] = frozenset()  # relative paths left out, directories with a trailing "/"
        self._cache: dict[str, tuple[tuple[int, int, int, int], Entry]] = {}
        self.kept_large: dict[str, Path] = {}  # a large entry's id -> a copy of its content, while one is kept (F27)

    def keep_large(self, world: str, into: Path, limit: int) -> None:
        """Copy every large file of ``world`` not kept yet into ``into``, so ``checkout`` can restore it (F27): its
        store keeps only a signature. A file that changed since ``world`` was taken, or cannot be read, is not
        copied, and stays unrestorable. Raises TooLarge, copying nothing, when the copies would pass ``limit`` bytes."""
        todo: list[tuple[Path, Entry]] = []
        for rel, entry in self.store.files(world):
            if entry.kind != "large" or entry.oid in self.kept_large:
                continue
            path = self.root / rel
            try:
                st = path.stat(follow_symlinks=False)
            except OSError:
                continue
            signature = (st.st_size, st.st_mtime_ns, st.st_ino, stat.S_IMODE(st.st_mode))
            if object_id("large", repr(signature).encode()) == entry.oid:
                todo.append((path, entry))
        kept = sum(p.stat().st_size for p in self.kept_large.values() if p.exists())
        wanted = sum(path.stat().st_size for path, _ in todo)
        if kept + wanted > limit:
            raise TooLarge(
                f"the workspace's files over {self.max_blob // 2**20} MB come to {(kept + wanted) / 2**30:.1f} GB, "
                f"more than the {limit / 2**30:.0f} GB frond copies so it can restore them between branches"
            )
        into.mkdir(parents=True, exist_ok=True)
        for path, entry in todo:
            copy = into / entry.oid
            try:
                shutil.copyfile(path, copy)
            except OSError:
                continue
            self.kept_large[entry.oid] = copy

    def release_large(self) -> None:
        """Delete the copies ``keep_large`` made."""
        for copy in self.kept_large.values():
            copy.unlink(missing_ok=True)
        self.kept_large.clear()

    def snapshot(self) -> str:
        """The directory's current state, as a tree id."""
        self._visited = 0
        return self._snapshot_dir(self.root, "", time.time_ns())

    def _snapshot_dir(self, path: Path | str, rel: str, started: int) -> str:
        entries: dict[str, Entry] = {}
        try:
            scan = list(os.scandir(path))
        except FileNotFoundError:
            scan = []
        for item in scan:
            name, key = item.name, f"{rel}{item.name}"
            if key in self.ignored or f"{key}/" in self.ignored:
                continue
            try:
                if item.is_symlink():
                    target = os.fsencode(os.readlink(item.path))
                    entries[name] = Entry("link", self.store.put("blob", target))
                elif item.is_dir(follow_symlinks=False):
                    if name not in self.exclude:
                        entries[name] = Entry("tree", self._snapshot_dir(item.path, f"{key}/", started))
                elif item.is_file(follow_symlinks=False):
                    entries[name] = self._file_entry(item, key, started)
            except FileNotFoundError:
                continue  # removed while the snapshot ran
            except PermissionError:  # unreadable: kept by its signature, like a large file, and never restored (F13)
                entries[name] = self._opaque(item)
        return self.store.put_tree(entries)

    @staticmethod
    def _opaque(item: os.DirEntry[str]) -> Entry:
        st = item.stat(follow_symlinks=False)
        mode = stat.S_IMODE(st.st_mode)
        return Entry("large", object_id("large", repr((st.st_size, st.st_mtime_ns, st.st_ino, mode)).encode()), mode)

    def _file_entry(self, item: os.DirEntry[str], key: str, started: int) -> Entry:
        self._visited += 1
        if self.max_files is not None and self._visited > self.max_files:
            raise TooLarge(f"{self.root} holds more than {self.max_files:,} files")
        st = item.stat(follow_symlinks=False)
        mode = stat.S_IMODE(st.st_mode)
        signature = (st.st_size, st.st_mtime_ns, st.st_ino, mode)
        cached = self._cache.get(key)
        if cached is not None and cached[0] == signature and started - st.st_mtime_ns > RACY_NS:
            return cached[1]
        if st.st_size > self.max_blob:
            entry = Entry("large", object_id("large", repr(signature).encode()), mode)
        else:
            with open(item.path, "rb") as f:
                entry = Entry("file", self.store.put("blob", f.read()), mode)
        self._cache[key] = (signature, entry)
        return entry

    # ── writing a world back ─────────────────────────────────────────────────

    def checkout(self, target: str, current: str | None = None) -> list[Change]:
        """Make the directory hold ``target``, touching only paths that differ; returns what changed."""
        if not target:  # "" is what a failed or switched-off snapshot returns, never a world: it would empty the tree
            raise ValueError("no world to check out: a snapshot that failed names none")
        current = current if current is not None else self.snapshot()
        changes = self.store.diff(current, target)
        for change in sorted(changes, key=lambda c: c.after is not None):  # removals first
            self.apply(change.path, change.after, change.before)
        return changes

    def read(self, path: str, entry: Entry | None) -> bytes | None:
        """The content an entry stands for (a link's target for links), or None for absent and large files."""
        if entry is None or entry.kind in ("tree", "large"):
            return None
        return self.store.blob(entry.oid)

    def apply(self, path: str, entry: Entry | None, previous: Entry | None = None) -> None:
        """Put one leaf in place: write a file, make a link or an empty directory, or remove it (entry None)."""
        target = self.root / path
        if entry is None or (previous is not None and previous.kind != entry.kind):
            self._remove(target, previous)
        if entry is None:
            self._prune(target.parent)
            return
        if entry.kind == "large":
            copy = self.kept_large.get(entry.oid)
            if copy is None:
                raise ValueError(f"{path} is too large to have been kept, so it cannot be restored")
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_symlink():
                target.unlink()
            fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.frond-")
            os.close(fd)
            shutil.copyfile(copy, tmp)
            os.chmod(tmp, entry.mode or 0o644)
            os.replace(tmp, target)
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        if entry.kind == "tree":
            target.mkdir(exist_ok=True)
        elif entry.kind == "link":
            if target.is_symlink() or target.exists():
                self._remove(target, None)
            os.symlink(os.fsdecode(self.store.blob(entry.oid)), target)
        else:
            if target.is_symlink():
                target.unlink()
            fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.frond-")
            with os.fdopen(fd, "wb") as f:
                f.write(self.store.blob(entry.oid))
            os.chmod(tmp, entry.mode or 0o644)
            os.replace(tmp, target)

    def _remove(self, target: Path, previous: Entry | None) -> None:
        """Remove a leaf this world tracked. A directory is removed only when it is a tracked, empty one: frond
        never deletes what it did not record (excluded caches, say)."""
        if target.is_symlink() or target.is_file():
            target.unlink(missing_ok=True)
        elif target.is_dir() and previous is not None and previous.kind == "tree" and not any(target.iterdir()):
            target.rmdir()

    def _prune(self, directory: Path) -> None:
        """Remove directories left empty by a removal, up to the root."""
        while directory != self.root and directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
            directory = directory.parent
