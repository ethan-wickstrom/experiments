"""A scripted language model: a canonical lm15 engine that replays prepared completions.

Used by the test-suite (deterministic, instant) and by ``frond --demo`` (paced like a real model, so the
whole UI can be seen working without an API key). The code in each scripted step really runs: files are
really edited and commands really execute, in whatever workspace the agent was started in.
"""

from __future__ import annotations

import json
import re
import threading
import time
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from typing import Any, Literal

import dspy
from dspy._vendor.lm15.types import StreamDeltaEvent, StreamEndEvent, StreamStartEvent, TextDelta
from dspy.lm15 import Message, Request, Response, TextPart, Usage


@dataclass(frozen=True, slots=True)
class Step:
    reasoning: str
    code: str

    def render(self) -> str:
        return (
            f"[[ ## note ## ]]\n{self.reasoning}\n\n[[ ## code ## ]]\n```python\n{self.code.strip()}\n```"
            "\n\n[[ ## completed ## ]]\n"
        )


@dataclass(frozen=True, slots=True)
class ToolStep:
    """A scripted step of the tools arm: one call (ledger B8)."""

    reasoning: str
    tool: str
    args: dict[str, Any]

    def render(self) -> str:
        return (
            f"[[ ## note ## ]]\n{self.reasoning}\n\n[[ ## tool ## ]]\n{self.tool}\n\n"
            f"[[ ## args ## ]]\n{json.dumps(self.args)}\n\n[[ ## completed ## ]]\n"
        )


@dataclass(frozen=True, slots=True)
class CutOff:
    """A scripted reply that stops at the output limit (finish reason "length"), as a runaway reply does (G38)."""

    text: str


def _request_text(request: Request) -> str:
    parts = []
    if request.system is not None:
        parts.append(
            request.system
            if isinstance(request.system, str)
            else "".join(getattr(p, "text", "") for p in request.system)
        )
    parts.extend(m.text or "" for m in request.messages)
    return "\n".join(parts)


class ScriptedEngine:
    def __init__(
        self,
        steps: Sequence[Step | ToolStep | CutOff | str] | None = None,
        *,
        chunk: int = 7,
        delay: float = 0.0,
        sub_answer: Callable[[str], str] | None = None,
        after_script: Callable[[str], Step] | None = None,
    ) -> None:
        self.steps: list[Step | ToolStep | CutOff | str] = list(steps or [])
        self.chunk = max(1, chunk)
        self.delay = delay
        self.sub_answer = sub_answer or (lambda prompt: "OK")
        self.after_script = after_script
        self.requests: list[Request] = []
        self._lock = threading.Lock()

    def add(self, *steps: Step | ToolStep | CutOff | str) -> None:
        with self._lock:
            self.steps.extend(steps)

    def _reply(self, request: Request) -> tuple[str, Literal["stop", "length"]]:
        """The completion for ``request`` and its finish reason."""
        text = self._completion(request)
        return (text.text, "length") if isinstance(text, CutOff) else (text, "stop")

    def _completion(self, request: Request) -> str | CutOff:
        text = _request_text(request)
        with self._lock:
            self.requests.append(request)
            if "[[ ## repl_history ## ]]" in text and ("[[ ## code ## ]]" in text or "[[ ## tool ## ]]" in text):
                if self.steps:
                    step = self.steps.pop(0)
                elif self.after_script is not None:
                    step = self.after_script(text)
                else:
                    step = Step("The script is finished.", "SUBMIT(response='(end of script)')")
                return step if isinstance(step, str | CutOff) else step.render()
            if "[[ ## repl_history ## ]]" in text:  # the extract fallback: answer its output fields directly
                block = re.search(r"Your output fields are:\n((?:\d+\. `\w+`[^\n]*\n?)+)", text)
                names = re.findall(r"`(\w+)`", block.group(1)) if block else ["response"]
                body = "".join(f"[[ ## {n} ## ]]\nI ran out of steps before finishing.\n\n" for n in names)
                return body + "[[ ## completed ## ]]\n"
        return self.sub_answer(text)

    @staticmethod
    def _usage(request: Request, completion: str) -> Usage:
        prompt_tokens = max(1, len(_request_text(request)) // 4)
        output_tokens = max(1, len(completion) // 4)
        return Usage(
            input_tokens=prompt_tokens,
            output_tokens=output_tokens,
            total_tokens=prompt_tokens + output_tokens,
        )

    def complete(self, request: Request) -> Response:
        text, finish = self._reply(request)
        return Response(
            id="scripted",
            model="frond-scripted",
            message=Message.assistant([TextPart(text)]),
            finish_reason=finish,
            usage=self._usage(request, text),
        )

    def stream(self, request: Request) -> Iterator[object]:
        text, finish = self._reply(request)
        yield StreamStartEvent(id="scripted", model="frond-scripted")
        for i in range(0, len(text), self.chunk):
            if self.delay:
                time.sleep(self.delay)
            yield StreamDeltaEvent(delta=TextDelta(text=text[i : i + self.chunk]))
        yield StreamEndEvent(finish_reason=finish, usage=self._usage(request, text))

    def close(self) -> None:
        pass


def scripted_lm(engine: ScriptedEngine) -> dspy.LM:
    return dspy.LM("openai/frond-scripted", engine=engine, cache=False, num_retries=0)
