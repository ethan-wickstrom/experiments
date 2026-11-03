"""Token streaming from DSPy into frond events.

DSPy streams LM output by handing chunks to ``settings.send_stream`` from inside an AnyIO worker thread.
:class:`StreamSink` is that object. It parses each reply's fields incrementally, as JSON (D53) or in ChatAdapter's
``[[ ## field ## ]]`` framing, so reasoning and code appear on screen as the model writes them, and it is also where
a cancelled turn aborts an in-flight LM call (by raising :class:`TurnCancelled` into DSPy's stream loop).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from frond.agent.control import TurnCancelled, TurnControl

MARKER = re.compile(r"\[\[ ## (\w+) ## \]\]")
_HEAD = "[[ ## "
_TAIL = " ## ]]"


def could_be_marker_prefix(s: str) -> bool:
    """True if ``s`` might be the beginning of a ``[[ ## name ## ]]`` marker that is still arriving."""
    if len(s) <= len(_HEAD):
        return _HEAD.startswith(s)
    if not s.startswith(_HEAD):
        return False
    rest = s[len(_HEAD) :]
    name = re.match(r"\w*", rest)
    tail = rest[name.end() if name else 0 :]
    return len(tail) < len(_TAIL) and _TAIL.startswith(tail)


class FieldStreamParser:
    """Splits a ChatAdapter completion into per-field text deltas as it streams in.

    Text is emitted as soon as it cannot be part of a marker. Leading newlines after a marker and trailing
    whitespace before the next one are dropped, matching how DSPy strips parsed field values.
    """

    def __init__(self, on_delta: Callable[[str, str], None]) -> None:
        self.on_delta = on_delta
        self.reset()

    def reset(self) -> None:
        self.buf = ""
        self.pos = 0
        self.field: str | None = None
        self.started = False
        self.pending_ws = ""

    def feed(self, text: str) -> None:
        self.buf += text
        while True:
            m = MARKER.search(self.buf, self.pos)
            if m:
                self._emit(self.buf[self.pos : m.start()], final=True)
                self.field, self.pos, self.started, self.pending_ws = m.group(1), m.end(), False, ""
                continue
            end = len(self.buf)
            i = self.buf.rfind("[[", self.pos)
            if i != -1 and could_be_marker_prefix(self.buf[i:]):
                end = i
            elif self.buf.endswith("["):
                end -= 1
            self._emit(self.buf[self.pos : end], final=False)
            self.pos = end
            return

    def _emit(self, text: str, *, final: bool) -> None:
        if self.field is None or self.field == "completed" or not text:
            return
        if not self.started:
            text = text.lstrip("\r\n")
            if not text:
                return
        body = text.rstrip()
        trailing = text[len(body) :]
        if not body:
            if not final:
                self.pending_ws += trailing
            return
        self.on_delta(self.field, self.pending_ws + body if self.started else body)
        self.started = True
        self.pending_ws = "" if final else trailing


_SUBMIT_START = re.compile(
    r"\A(?:\s*(?:```[\w-]*\s*\n)?)(?:\s*#[^\n]*\n)*\s*SUBMIT\(\s*(?:response\s*=\s*)?"
    r"(?P<prefix>[rRuUfF]{0,2})(?P<quote>\"\"\"|'''|\"|')"
)
_ESCAPES = {"n": "\n", "t": "\t", "r": "", "\\": "\\", '"': '"', "'": "'", "\n": ""}


class SubmitStreamer:
    """Streams the string literal of a step that is just ``SUBMIT(response=\"\"\"...\"\"\")``.

    The final answer is written as Python code, so without this the user would watch a code block fill
    up and then see the same text again. Decoding the literal as it arrives lets the answer stream as
    prose. Anything unusual (computed responses, code before SUBMIT) simply isn't streamed.
    """

    def __init__(self, on_text: Callable[[str], None]) -> None:
        self.on_text = on_text
        self.reset()

    def reset(self) -> None:
        self.code = ""
        self.state = "search"  # search → stream → done
        self.quote = ""
        self.raw = False
        self.cursor = 0

    def feed(self, code_delta: str) -> None:
        if self.state == "done":
            return
        self.code += code_delta
        if self.state == "search":
            m = _SUBMIT_START.match(self.code)
            if m is None:
                stripped = self.code.lstrip()
                if len(stripped) > 200 or (stripped and not _could_start_submit(stripped)):
                    self.state = "done"
                return
            quote = m.group("quote")
            rest = self.code[m.end() :]
            if len(quote) == 1 and len(rest) < 2 and rest == quote * len(rest):
                return  # could still become a triple quote
            self.state = "stream"
            self.quote = quote
            self.raw = "r" in m.group("prefix").lower()
            self.cursor = m.end()
        self._advance()

    def _advance(self) -> None:
        out: list[str] = []
        code, q, i = self.code, self.quote, self.cursor
        while i < len(code):
            ch = code[i]
            if ch == "\\" and not self.raw:
                if i + 1 >= len(code):
                    break  # wait for the escaped character
                nxt = code[i + 1]
                out.append(_ESCAPES.get(nxt, "\\" + nxt))
                i += 2
                continue
            if code.startswith(q, i):
                self.state = "done"
                i += len(q)
                break
            if len(q) == 3 and ch == q[0] and len(code) - i < 3:
                break  # might be the closing quotes, still arriving
            out.append(ch)
            i += 1
        self.cursor = i
        if out:
            self.on_text("".join(out))


def _could_start_submit(text: str) -> bool:
    """Whether ``text`` (non-empty, left-stripped) might still turn into a leading SUBMIT call."""
    if "```".startswith(text):
        return True
    if text.startswith("```"):
        _first_line, _, rest = text.partition("\n")
        return not rest.strip() or _could_start_submit(rest.lstrip())
    if text.startswith("#"):
        return True
    target = "SUBMIT("
    return target.startswith(text[: len(target)]) if len(text) < len(target) else text.startswith(target)


_JSON_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", '"': '"', "\\": "\\", "/": "/"}


def _unit(buf: str, i: int) -> int | None:
    """The code unit of the ``\\uXXXX`` escape at ``buf[i]``, or None while it is incomplete or not one."""
    text = buf[i + 2 : i + 6]
    if buf[i : i + 2] != "\\u" or len(text) < 4:
        return None
    try:
        return int(text, 16)
    except ValueError:
        return None


class JsonFieldStreamParser:
    """Splits a JSON reply of string fields (the json protocol, D53) into per-field text deltas as it streams in:
    each value's decoded characters are emitted as they arrive, an escape only once it is whole."""

    def __init__(self, on_delta: Callable[[str, str], None]) -> None:
        self.on_delta = on_delta
        self.reset()

    def reset(self) -> None:
        self.buf = ""
        self.state = "between"  # between | key | colon | value | string | skip
        self.key = ""
        self.field: str | None = None

    def feed(self, text: str) -> None:
        self.buf += text
        i = 0
        out: list[str] = []
        while i < len(self.buf):
            c = self.buf[i]
            if self.state in ("key", "string"):
                if c == '"':
                    if self.state == "key":
                        self.field, self.state = self.key, "colon"
                    else:
                        self.state = "between"
                    i += 1
                    continue
                if c == "\\":
                    if i + 1 >= len(self.buf):
                        break
                    e = self.buf[i + 1]
                    if e == "u":
                        unit = _unit(self.buf, i)
                        if unit is None:
                            break
                        char, i = chr(unit), i + 6
                        if 0xD800 <= unit < 0xDC00:  # a surrogate pair is one character: wait for its low half
                            low = _unit(self.buf, i)
                            if low is None:
                                if len(self.buf) - i < 6:
                                    i -= 6
                                    break
                            elif 0xDC00 <= low < 0xE000:
                                char, i = chr(0x10000 + ((unit - 0xD800) << 10) + (low - 0xDC00)), i + 6
                    else:
                        char, i = _JSON_ESCAPES.get(e, e), i + 2
                else:
                    char, i = c, i + 1
                if self.state == "key":
                    self.key += char
                else:
                    out.append(char)
                continue
            self._flush(out)
            if self.state == "between" and c == '"':
                self.key, self.state = "", "key"
            elif self.state == "colon" and c == ":":
                self.state = "value"
            elif self.state == "value" and not c.isspace():
                self.state = "string" if c == '"' else "skip"
            elif self.state == "skip" and c in ",}":
                self.state = "between"
            i += 1
        self._flush(out)
        self.buf = self.buf[i:]

    def _flush(self, out: list[str]) -> None:
        if out and self.field is not None:
            self.on_delta(self.field, "".join(out))
        out.clear()


class ReplyStreamParser:
    """Per-field deltas of a reply in either protocol: JSON when its first visible character opens an object,
    DSPy's field markers otherwise (D53)."""

    def __init__(self, on_delta: Callable[[str, str], None]) -> None:
        self.markers = FieldStreamParser(on_delta)
        self.json = JsonFieldStreamParser(on_delta)
        self.reset()

    def reset(self) -> None:
        self.markers.reset()
        self.json.reset()
        self.chosen: FieldStreamParser | JsonFieldStreamParser | None = None
        self.held = ""

    def feed(self, text: str) -> None:
        if self.chosen is None:
            self.held += text
            visible = self.held.lstrip()
            if not visible:
                return
            self.chosen = self.json if visible.startswith("{") else self.markers
            text, self.held = self.held, ""
        self.chosen.feed(text)


class StreamSink:
    """The ``send_stream`` object DSPy writes chunks to. One per agent; re-armed before each LM call."""

    def __init__(
        self,
        control: TurnControl,
        on_field: Callable[[str, str], None],
        on_thinking: Callable[[str], None] | None = None,
    ) -> None:
        self.control = control
        self.parser = ReplyStreamParser(on_field)
        self.call = JsonFieldStreamParser(on_field)  # a native tool call's arguments: its note, and submit's reply
        self.on_thinking = on_thinking
        self.active = True

    def arm(self) -> None:
        self.parser.reset()
        self.call.reset()

    async def send(self, chunk: Any) -> None:
        if self.control.cancelled():
            raise TurnCancelled()
        try:
            delta = chunk.choices[0].delta
        except (AttributeError, IndexError, KeyError, TypeError):
            return
        content = _get(delta, "content")
        thinking = _get(delta, "reasoning_content")
        if thinking and self.on_thinking is not None:
            self.on_thinking(thinking)
        if content:
            self.parser.feed(content)
        for call in _get(delta, "tool_calls") or []:  # native tool calls (B19): the first is the step's
            arguments = _get(_get(call, "function") or {}, "arguments")
            if arguments and (_get(call, "index") or 0) == 0:
                self.call.feed(arguments)


def _get(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)
