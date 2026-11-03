"""What the agent may do without asking.

The default ("auto") lets the agent edit files inside the workspace and run ordinary commands freely,
and asks the user before anything that is hard to undo: recursive deletes, history-rewriting git
operations, privilege escalation, piping downloads into a shell, or writing outside the workspace.
"""

from __future__ import annotations

import re
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

type Mode = Literal["auto", "yolo", "readonly"]
type Decision = Literal["yes", "always", "no"]
type Approver = Callable[[str, str], Decision]

RISKY_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(p), why)
    for p, why in (
        (r"\brm\s+(-\S*[rRf]\S*\s+)+", "recursive or forced delete"),
        (r"\bgit\s+reset\s+--hard\b", "discards uncommitted work"),
        (r"\bgit\s+clean\s+-\S*[fdx]", "deletes untracked files"),
        (r"\bgit\s+push\b.*(--force\b|--force-with-lease\b|\s-f\b)", "force push"),
        (r"\bgit\s+(checkout|restore)\s+(--\s|\.\s*$|-- \.)", "discards local changes"),
        (r"\bgit\s+stash\s+(drop|clear)\b", "drops stashed work"),
        (r"\bgit\s+branch\s+-D\b", "force-deletes a branch"),
        (r"\bgit\s+push\b", "publishes commits to a remote"),
        (r"\bsudo\b|\bdoas\b", "privilege escalation"),
        (r"\b(mkfs|fdisk|diskutil|shutdown|reboot|halt|poweroff)\b", "system-level operation"),
        (r"\bdd\s+.*\bof=", "raw disk write"),
        (r"(curl|wget)\b[^|;&]*\|\s*(sudo\s+)?(ba|z|k)?sh\b", "pipes a download into a shell"),
        (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}", "fork bomb"),
        (r"\bchmod\s+-R\b|\bchown\s+-R\b", "recursive permission change"),
        (r">\s*/dev/sd[a-z]", "raw disk write"),
        (
            r"\b(npm|pnpm|yarn)\s+publish\b|\buv\s+publish\b|\btwine\s+upload\b|\bcargo\s+publish\b",
            "publishes a package",
        ),
    )
)


def risky_reason(command: str) -> str | None:
    for pattern, why in RISKY_PATTERNS:
        if pattern.search(command):
            return why
    return None


@dataclass
class Policy:
    mode: Mode = "auto"
    approver: Approver | None = None
    _always: set[str] = field(default_factory=set)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def check_write(self, path: Path, inside_workspace: bool) -> None:
        if self.mode == "readonly":
            raise PermissionError("frond is in read-only mode: file changes are disabled")
        if not inside_workspace:
            self._ask("Write outside the workspace", str(path), key=f"write:{path}")

    def check_delete_tree(self, path: Path, detail: str) -> None:
        """Deleting a directory and its contents asks first, as ``rm -rf`` does."""
        self._ask("Delete a directory and its contents", detail, key=f"rmtree:{path}")

    def check_command(self, command: str) -> None:
        if self.mode == "readonly":
            raise PermissionError("frond is in read-only mode: commands are disabled")
        reason = risky_reason(command)
        if reason is not None:
            self._ask(f"Run command ({reason})", command, key=f"cmd:{command.strip()}")

    def _ask(self, title: str, detail: str, *, key: str) -> None:
        if self.mode == "yolo":
            return
        with self._lock:
            if key in self._always:
                return
        if self.approver is None:
            raise PermissionError(
                f"{title} needs the user's approval, which is not available here: {detail!r}. "
                "Explain to the user what you wanted to do and why, and let them run it."
            )
        decision = self.approver(title, detail)
        if decision == "always":
            with self._lock:
                self._always.add(key)
            return
        if decision != "yes":
            raise PermissionError(f"The user declined: {title}: {detail!r}. Do not retry it; adjust your approach.")
