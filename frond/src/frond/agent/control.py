"""Turn-level control shared by the agent loop, the REPL, the tools, and the LM stream."""

from __future__ import annotations

import threading


class TurnCancelled(BaseException):
    """Raised inside the agent thread to unwind a turn the user stopped.

    A BaseException so that no ``except Exception`` along the way (DSPy's included) swallows it.
    """


class TurnControl:
    def __init__(self) -> None:
        self._cancel = threading.Event()

    def cancel(self) -> None:
        self._cancel.set()

    def reset(self) -> None:
        self._cancel.clear()

    def cancelled(self) -> bool:
        return self._cancel.is_set()

    def check(self) -> None:
        if self._cancel.is_set():
            raise TurnCancelled()
