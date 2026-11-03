"""Headless output for ``frond -p``: progress as a compact log on stderr, the answer on stdout.

``--json`` instead writes every event as one JSON object per line on stdout, which makes frond easy to
drive from scripts (and from other agents).
"""

from __future__ import annotations

import dataclasses
import json
import sys
from collections.abc import Callable
from typing import TextIO

from frond import events as ev

_RESET = "\x1b[0m"
_DIM = "\x1b[2m"
_GREEN = "\x1b[32m"
_RED = "\x1b[31m"
_YELLOW = "\x1b[33m"
_CYAN = "\x1b[36m"


class Printer:
    def __init__(
        self,
        out: TextIO | None = None,
        err: TextIO | None = None,
        *,
        color: bool | None = None,
        json_mode: bool = False,
        verbose: bool = False,
        redact: Callable[[str], str] | None = None,
    ) -> None:
        self.redact = redact or (lambda text: text)  # secrets out of what a harness may store (ledger B12)
        self.out = out or sys.stdout
        self.err = err or sys.stderr
        self.color = self.err.isatty() if color is None else color
        self.json_mode = json_mode
        self.verbose = verbose
        self.final: ev.TurnFinished | None = None
        self._reasoning: dict[int, str] = {}

    def c(self, code: str, text: str) -> str:
        return f"{code}{text}{_RESET}" if self.color else text

    def log(self, text: str) -> None:
        print(self.redact(text), file=self.err, flush=True)

    def __call__(self, event: ev.Event) -> None:
        if self.json_mode:
            payload = {"type": type(event).__name__, **dataclasses.asdict(event)}
            print(self.redact(json.dumps(payload, default=str)), file=self.out, flush=True)
            if isinstance(event, ev.TurnFinished):
                self.final = event
            return
        match event:
            case ev.StepPlanned(step=step, reasoning=reasoning, code=code):
                first = next((line for line in reasoning.splitlines() if line.strip()), "")
                self.log(self.c(_DIM, f"· step {step}") + f"  {first[:200]}")
                if self.verbose and code:
                    for line in code.splitlines():
                        self.log(self.c(_DIM, f"    {line}"))
            case ev.CommandStarted(command=command, background=background):
                self.log(self.c(_CYAN, "  $ ") + command.replace("\n", " ⏎ ") + (" &" if background else ""))
            case ev.CommandFinished(status=status, exit_code=code, duration=duration):
                mark = {
                    "ok": self.c(_GREEN, "ok"),
                    "failed": self.c(_RED, f"exit {code}"),
                    "timeout": self.c(_YELLOW, "timeout"),
                    "cancelled": self.c(_YELLOW, "stopped"),
                    "background": self.c(_CYAN, "background"),
                }[status]
                self.log(f"    → {mark} {self.c(_DIM, f'{duration:.1f}s')}")
            case ev.FileChanged(path=path, kind=kind, added=added, removed=removed):
                self.log(
                    f"  {self.c(_YELLOW, '✎')} {kind} {path} "
                    + self.c(_GREEN, f"+{added}")
                    + " "
                    + self.c(_RED, f"−{removed}")
                )
            case ev.ExecFinished(error=error) if error:
                self.log(self.c(_RED, "    " + error.strip().splitlines()[-1][:300]))
            case ev.SubAgentStarted(task=task):
                self.log(self.c(_CYAN, "  ◇ subagent: ") + task.splitlines()[0][:160])
            case ev.Folded(steps=steps):
                self.log(self.c(_DIM, f"  (folded {steps} earlier steps into an index)"))
            case ev.Notice(level=level, text=text):
                self.log(self.c(_YELLOW if level != "error" else _RED, text))
            case ev.TurnFinished(response=response, status=status, error=error, duration=duration, steps=steps):
                self.final = event
                summary = f"{status} · {steps} step{'s' if steps != 1 else ''} · {duration:.1f}s"
                self.log(self.c(_GREEN if status == "done" else _YELLOW, "◆ ") + self.c(_DIM, summary))
                if error:
                    self.log(self.c(_RED, error))
                if response:
                    print(self.redact(response), file=self.out, flush=True)
            case _:
                pass
