"""Scopes as savepoints (design.md "Context management", hypothesis H5, ledger B9).

The model opens a scope when it starts a subtask of several steps and closes it with a result, or abandons it:
- closing replaces the scope's steps in the model's context with one entry, goal → result (Spine's move). The steps
  stay in the step log, and since a closed scope is the tail of the history, the cached prompt prefix before it
  survives;
- abandoning reverts the workspace changes made inside it by a three-way merge, so later edits by others stay; cuts
  the context back to where the scope opened; and keeps the reason as a note, which AgentRewind found its rewinds
  needed. REPL names changed since the savepoint are listed as stale, since a namespace cannot be rewound cheaply.

The tools record each operation here; the loop applies it to the history at the start of the next step
(``FrondRLM._apply_scopes``).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Scope:
    goal: str
    step: int  # the step that opened it: its entries are those from this step on
    world: str  # the workspace when it opened ("" when snapshots are off)
    names: list[str] = field(default_factory=list)  # the REPL's names digest then


@dataclass
class ScopeOp:
    kind: Literal["close", "abandon"]
    scope: Scope
    text: str  # the result, or the reason
    note: str = ""  # abandon: what the revert did and which REPL names are now stale


class Scopes:
    def __init__(self) -> None:
        self.stack: list[Scope] = []
        self._pending: list[ScopeOp] = []
        self._lock = threading.Lock()
        self.opened = self.closed = self.abandoned = 0

    def reset(self) -> None:
        """A new turn: scopes do not outlive the turn that opened them."""
        with self._lock:
            self.stack.clear()
            self._pending.clear()

    def open(self, goal: str, step: int, world: str, names: list[str]) -> int:
        with self._lock:
            self.stack.append(Scope(goal, step, world, names))
            self.opened += 1
            return len(self.stack)

    def end(self, kind: Literal["close", "abandon"], text: str, note: str = "") -> Scope:
        """Close or abandon the innermost open scope; the history changes at the start of the next step."""
        with self._lock:
            if not self.stack:
                raise ValueError("there is no open scope; call open_scope(goal) when you start a subtask")
            scope = self.stack.pop()
            self._pending.append(ScopeOp(kind, scope, text, note))
            if kind == "close":
                self.closed += 1
            else:
                self.abandoned += 1
            return scope

    def innermost(self) -> Scope | None:
        with self._lock:
            return self.stack[-1] if self.stack else None

    def take(self) -> list[ScopeOp]:
        with self._lock:
            pending, self._pending = self._pending, []
            return pending

    def describe(self) -> str:
        """The prompt field: the open scopes, outermost first."""
        with self._lock:
            if not self.stack:
                return "(none)"
            return "\n".join(f"{i}. {s.goal} (opened at step {s.step})" for i, s in enumerate(self.stack, start=1))
