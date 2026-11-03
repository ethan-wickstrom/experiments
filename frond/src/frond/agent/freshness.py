"""What the model has seen of each file this turn, and whether it still holds (design.md, "Freshness is truth
maintenance"; hypothesis H3, ledger B5).

Each ``view`` or ``read`` records an observation: the path, the blob id (``world.object_id``) of the bytes the model
saw, and the step. The observation is fresh while the file still holds those bytes. It goes stale when anything else
changes the file: the model's own shell command, a formatter, a background job, the user. The model's own edits keep
it fresh, since the model knows what it wrote, unless the observation was already stale.

With freshness on, the model is told before each step which of its reads are stale, and a whole-file write or a
delete over a stale read is refused until it reads the file again, so a change it never saw cannot be overwritten.
With it off, frond only counts stale actions, so the two arms of H3 are measured alike.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

from frond.world.store import object_id

ABSENT = ""  # the oid of a file that is not there


@dataclass(frozen=True, slots=True)
class Observation:
    path: str  # as the model names it (workspace-relative)
    oid: str  # what the model saw: the blob id of the bytes, ABSENT when it saw no file
    step: int


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
        self._lock = threading.Lock()

    def reset(self) -> None:
        """A new turn: the model's picture is what it reads from now on."""
        with self._lock:
            self._seen.clear()
            self.step = 0

    def saw(self, path: str, data: bytes) -> None:
        with self._lock:
            self._seen[path] = Observation(path, object_id("blob", data), self.step)

    def changed(self, path: str) -> Observation | None:
        """The observation of ``path`` when the file no longer holds what the model saw; None when fresh or unread."""
        with self._lock:
            seen = self._seen.get(path)
        if seen is None or current_oid(self.root / path) == seen.oid:
            return None
        return seen

    def stale(self) -> list[Observation]:
        with self._lock:
            seen = list(self._seen.values())
        return [o for o in seen if current_oid(self.root / o.path) != o.oid]

    def note(self) -> str:
        """The prompt field: each stale read, and when it was made."""
        stale = self.stale()
        if not stale:
            return "(none)"
        return "\n".join(f"- {o.path} (read at step {o.step}; it has changed since)" for o in stale)
