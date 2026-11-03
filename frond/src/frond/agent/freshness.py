"""What the model has seen of each file this turn, and whether it still holds (design.md, "Freshness is truth
maintenance"; hypothesis H3, ledger B5).

Each ``view`` or ``read`` records an observation: the path, the blob id (``world.object_id``) of the bytes the model
saw, and the step. The observation is fresh while the file still holds those bytes. It goes stale when anything else
changes the file: the model's own shell command, a formatter, a background job, the user. The model's own edits keep
it fresh, since the model knows what it wrote, unless the observation was already stale.

With freshness on, the model is told before each step which of its reads are stale, and a whole-file write or a
delete over a stale read is refused until it reads the file again, so a change it never saw cannot be overwritten.
With it off, frond only counts stale actions, so the two arms of H3 are measured alike.

An observation is of a file, not of a name: it is keyed by the file's real path, so a symlink and its target share
one (F17), and a file outside the workspace is checked where it is (F21). A read through a symlink also remembers
where the name led, so a name that now leads elsewhere counts as unseen (review of #24). The model's own delete or
move records the file as absent where it was, and a move carries each read, fresh or stale, to the new place (F18).
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from pathlib import Path

from frond.world.store import object_id

ABSENT = ""  # the oid of a file that is not there


@dataclass(frozen=True, slots=True)
class Observation:
    path: str  # as the model last named it, for messages
    oid: str  # what the model saw: the blob id of the bytes, ABSENT when it saw no file
    step: int
    real: str = ""  # the file's real path, which keys the observation


def current_oid(path: Path) -> str:
    try:
        return object_id("blob", path.read_bytes())
    except (FileNotFoundError, NotADirectoryError):
        return ABSENT
    except OSError:
        return "?"  # unreadable (a directory now, permissions): not what the model saw


class Observations:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.step = 0
        self._seen: dict[str, Observation] = {}
        self._names: dict[str, tuple[str, str]] = {}  # a name read through a symlink -> (the real path, as named)
        self._lock = threading.Lock()

    def reset(self) -> None:
        """A new turn: the model's picture is what it reads from now on."""
        with self._lock:
            self._seen.clear()
            self._names.clear()
            self.step = 0

    def real(self, path: str | Path) -> str:
        """The real path of ``path`` (workspace-relative, ``~/``-prefixed or absolute), symlinks followed."""
        p = Path(path).expanduser()
        return os.path.realpath(p if p.is_absolute() else self.root / p)

    def lexical(self, path: str | Path) -> str:
        """``path`` made absolute and normalized, symlinks not followed: the name as the model gave it."""
        p = Path(path).expanduser()
        return os.path.normpath(p if p.is_absolute() else self.root / p)

    def saw(self, path: str | Path, data: bytes, display: str | None = None) -> None:
        real, name = self.real(path), self.lexical(path)
        with self._lock:
            self._seen[real] = Observation(display or str(path), object_id("blob", data), self.step, real)
            if name != real:
                self._names[name] = (real, display or str(path))

    def absent(self, path: str | Path, display: str | None = None) -> None:
        """The model's own action removed the file: its picture, no file there, is true."""
        real = self.real(path)
        with self._lock:
            self._seen[real] = Observation(display or str(path), ABSENT, self.step, real)

    def changed(self, path: str | Path) -> Observation | None:
        """The observation of ``path`` when the file no longer holds what the model saw, or when the name it read
        through now leads to another file; None when fresh or unread."""
        real, name = self.real(path), self.lexical(path)
        with self._lock:
            then = self._names.get(name)
            if then is not None and then[0] != real and then[0] in self._seen:
                return self._seen[then[0]]  # retargeted since the read: what it leads to now was never seen
            seen = self._seen.get(real)
        if seen is None or current_oid(Path(real)) == seen.oid:
            return None
        return seen

    def within(self, directory: str | Path) -> list[Observation]:
        """The observations of files inside ``directory``."""
        prefix = self.real(directory).rstrip("/") + "/"
        with self._lock:
            return [o for key, o in self._seen.items() if key.startswith(prefix)]

    def moved(self, source: str | Path, target: str | Path, display: str) -> None:
        """The model moved ``source`` (a file or a directory, not a symlink) to ``target``: what it had read there
        is now absent, and each read goes with the file, fresh or stale as it was."""
        old, new = self.real(source).rstrip("/"), os.path.realpath(target)
        with self._lock:
            moving = [(key, o) for key, o in self._seen.items() if key == old or key.startswith(old + "/")]
            for key, o in moving:  # named as the model named the target, plus the file's place in a moved directory
                self._seen[key] = Observation(o.path, ABSENT, self.step, key)
                self._seen[new + key[len(old) :]] = Observation(
                    display + key[len(old) :], o.oid, o.step, new + key[len(old) :]
                )
            self.forget_names(old)

    def forget_names(self, path: str | Path) -> None:
        """Names at or under ``path`` no longer lead anywhere the model read through (the model moved them)."""
        prefix = self.lexical(path).rstrip("/")
        for name in [n for n in self._names if n == prefix or n.startswith(prefix + "/")]:
            del self._names[name]

    def stale(self) -> list[Observation]:
        with self._lock:
            seen, names = dict(self._seen), list(self._names.items())
        out = [o for o in seen.values() if current_oid(Path(o.real)) != o.oid]
        for name, (then, display) in names:
            if os.path.realpath(name) != then and then in seen:  # a name that now leads to a file never read
                out.append(Observation(display, seen[then].oid, seen[then].step, then))
        return out

    def note(self) -> str:
        """The prompt field: each stale read, and when it was made."""
        stale = self.stale()
        if not stale:
            return "(none)"
        return "\n".join(f"- {o.path} (read at step {o.step}; it has changed since)" for o in stale)
