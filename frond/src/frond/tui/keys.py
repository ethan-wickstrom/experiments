"""Decoding terminal input bytes into key, mouse, paste and focus events.

The decoder is a pure state machine (bytes in, events out) so it can be tested without a terminal. It
understands legacy xterm sequences, the kitty keyboard protocol's ``CSI ... u`` form (which makes Esc
and Shift+Enter unambiguous where supported), SGR mouse reports, and bracketed paste.
"""

from __future__ import annotations

import codecs
import re
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class Key:
    name: str  # "a", "enter", "up", "f5", ... (lower-case); printable keys use the character itself
    ctrl: bool = False
    alt: bool = False
    shift: bool = False

    @property
    def char(self) -> str | None:
        """The text this key types, if it is a plain printable key."""
        if self.ctrl or self.alt or len(self.name) != 1:
            return None
        return self.name

    def __str__(self) -> str:
        mods = "".join(m for m, on in (("ctrl+", self.ctrl), ("alt+", self.alt), ("shift+", self.shift)) if on)
        return mods + self.name


@dataclass(frozen=True, slots=True)
class Mouse:
    kind: Literal["press", "release", "drag", "wheel_up", "wheel_down", "move"]
    x: int
    y: int
    button: int = 0
    shift: bool = False
    alt: bool = False
    ctrl: bool = False


@dataclass(frozen=True, slots=True)
class Paste:
    text: str


@dataclass(frozen=True, slots=True)
class Focus:
    gained: bool


type InputEvent = Key | Mouse | Paste | Focus

_CSI_TILDE = {
    1: "home",
    2: "insert",
    3: "delete",
    4: "end",
    5: "pageup",
    6: "pagedown",
    7: "home",
    8: "end",
    11: "f1",
    12: "f2",
    13: "f3",
    14: "f4",
    15: "f5",
    17: "f6",
    18: "f7",
    19: "f8",
    20: "f9",
    21: "f10",
    23: "f11",
    24: "f12",
}
_CSI_LETTER = {
    "A": "up",
    "B": "down",
    "C": "right",
    "D": "left",
    "H": "home",
    "F": "end",
    "P": "f1",
    "Q": "f2",
    "R": "f3",
    "S": "f4",
    "Z": "tab",
}
_KITTY_FUNCTIONAL = {
    9: "tab",
    13: "enter",
    27: "escape",
    127: "backspace",
    57399: "0",
    57414: "enter",
    57417: "left",
    57418: "right",
    57419: "up",
    57420: "down",
    57421: "pageup",
    57422: "pagedown",
    57423: "home",
    57424: "end",
    57425: "insert",
    57426: "delete",
}
_CSI_RE = re.compile(rb"\x1b\[([<?>=]?)([\d;:]*)([\x20-\x2f]*)([\x40-\x7e])")
_PASTE_END = b"\x1b[201~"


def _mods(value: int) -> tuple[bool, bool, bool]:
    """Decode an xterm/kitty modifier parameter into (shift, alt, ctrl)."""
    bits = max(0, value - 1)
    return bool(bits & 1), bool(bits & 2), bool(bits & 4)


def _control_key(byte: int) -> Key:
    if byte in (0x0D,):
        return Key("enter")
    if byte == 0x0A:
        return Key("j", ctrl=True)  # Ctrl+J (line feed): frond uses it to insert a newline
    if byte == 0x09:
        return Key("tab")
    if byte in (0x7F, 0x08):
        return Key("backspace")
    if byte == 0x1B:
        return Key("escape")
    if byte == 0x00:
        return Key("space", ctrl=True)
    if 1 <= byte <= 26:
        return Key(chr(byte + 96), ctrl=True)
    return Key({0x1C: "\\", 0x1D: "]", 0x1E: "^", 0x1F: "_"}.get(byte, "?"), ctrl=True)


class Decoder:
    """Feed it bytes as they arrive; it returns complete events and buffers partial sequences."""

    def __init__(self) -> None:
        self.buf = b""
        self.paste: bytearray | None = None
        self._utf8 = codecs.getincrementaldecoder("utf-8")(errors="replace")

    def pending(self) -> bool:
        """True when bytes are waiting that might be the start of a longer sequence (e.g. a lone Esc)."""
        return bool(self.buf) or self.paste is not None

    def flush(self) -> list[InputEvent]:
        """Interpret whatever is buffered as complete: called after a short quiet period (lone Esc)."""
        if self.paste is not None:
            return []
        events: list[InputEvent] = []
        buf, self.buf = self.buf, b""
        if buf.startswith(b"\x1b"):
            events.append(Key("escape"))
            buf = buf[1:]
        if buf:
            events.extend(self.feed(buf))
        return events

    def feed(self, data: bytes) -> list[InputEvent]:
        self.buf += data
        events: list[InputEvent] = []
        while self.buf:
            if self.paste is not None:
                end = self.buf.find(_PASTE_END)
                if end == -1:
                    keep = len(_PASTE_END) - 1
                    self.paste += self.buf[:-keep] if len(self.buf) > keep else b""
                    self.buf = self.buf[-keep:] if len(self.buf) > keep else self.buf
                    break
                self.paste += self.buf[:end]
                self.buf = self.buf[end + len(_PASTE_END) :]
                text = bytes(self.paste).decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
                self.paste = None
                events.append(Paste(text))
                continue
            first = self.buf[0]
            if first == 0x1B:
                consumed, event = self._escape()
                if consumed == 0:
                    break  # incomplete: wait for more bytes (or flush())
                self.buf = self.buf[consumed:]
                if event is not None:
                    events.append(event)
                continue
            if first < 0x20 or first == 0x7F:
                self.buf = self.buf[1:]
                events.append(_control_key(first))
                continue
            # A run of printable bytes: decode UTF-8 (possibly split across reads).
            end = 0
            while end < len(self.buf) and self.buf[end] >= 0x20 and self.buf[end] != 0x7F:
                end += 1
            text = self._utf8.decode(self.buf[:end])
            self.buf = self.buf[end:]
            events.extend(Key(ch) for ch in text)
        return events

    def _escape(self) -> tuple[int, InputEvent | None]:
        buf = self.buf
        if len(buf) == 1:
            return 0, None
        second = buf[1]
        if second == ord("["):
            if buf.startswith(b"\x1b[200~"):
                self.paste = bytearray()
                return 6, None
            if buf.startswith(b"\x1b[M"):  # legacy X10 mouse: ESC [ M b x y
                if len(buf) < 6:
                    return 0, None
                return 6, self._mouse_x10(buf[3] - 32, buf[4] - 32, buf[5] - 32)
            m = _CSI_RE.match(buf)
            if m is None:
                if len(buf) > 32 or not re.fullmatch(rb"\x1b\[[<?>=]?[\d;:]*[\x20-\x2f]*", buf):
                    return 1, Key("escape")  # garbage: treat the Esc as a key and resync
                return 0, None
            return m.end(), self._csi(m.group(1).decode(), m.group(2).decode(), m.group(4).decode())
        if second == ord("O"):
            if len(buf) < 3:
                return 0, None
            name = {
                "A": "up",
                "B": "down",
                "C": "right",
                "D": "left",
                "H": "home",
                "F": "end",
                "P": "f1",
                "Q": "f2",
                "R": "f3",
                "S": "f4",
                "M": "enter",
            }.get(chr(buf[2]))
            return 3, Key(name) if name else None
        if second == ord("]"):  # OSC reply (e.g. colour query): swallow through BEL or ST
            for terminator in (b"\x07", b"\x1b\\"):
                end = buf.find(terminator)
                if end != -1:
                    return end + len(terminator), None
            return (0, None) if len(buf) < 512 else (len(buf), None)
        if second == 0x1B:
            return 1, Key("escape")
        # Alt+key: ESC followed by a key.
        if second == 0x0D:
            return 2, Key("enter", alt=True)
        if second < 0x20 or second == 0x7F:
            key = _control_key(second)
            return 2, Key(key.name, ctrl=key.ctrl, alt=True)
        ch_len = 1
        if second >= 0xC0:
            ch_len = 2 if second < 0xE0 else 3 if second < 0xF0 else 4
            if len(buf) < 1 + ch_len:
                return 0, None
        ch = buf[1 : 1 + ch_len].decode("utf-8", errors="replace")
        return 1 + ch_len, Key(ch.lower() if ch.isalpha() else ch, alt=True, shift=ch.isupper())

    def _csi(self, private: str, params: str, final: str) -> InputEvent | None:
        if private == "<" and final in "Mm":
            parts = [int(p or 0) for p in params.split(";")[:3]]
            if len(parts) < 3:
                return None
            return self._mouse_sgr(parts[0], parts[1], parts[2], final == "m")
        if private:
            return None  # other private replies (DA, kitty flag queries): ignore
        if final == "I":
            return Focus(True)
        if final == "O":
            return Focus(False)
        fields = [p.split(":")[0] for p in params.split(";")] if params else []
        nums = [int(f) if f.isdigit() else 0 for f in fields]
        mods = nums[1] if len(nums) > 1 else 1
        shift, alt, ctrl = _mods(mods)
        if final == "u":
            code = nums[0] if nums else 0
            name = _KITTY_FUNCTIONAL.get(code)
            if name is None:
                if code < 32 or code > 0x10FFFF:
                    return None
                name = chr(code)
                if shift and name.isalpha():
                    name = name.lower()
                elif shift and not ctrl and not alt:
                    shift = False  # shifted symbols arrive as the symbol itself
            return Key(name, ctrl=ctrl, alt=alt, shift=shift)
        if final == "~":
            code = nums[0] if nums else 0
            if code == 27 and len(nums) >= 3:  # xterm modifyOtherKeys: CSI 27 ; mods ; code ~
                shift, alt, ctrl = _mods(nums[1])
                name = _KITTY_FUNCTIONAL.get(nums[2]) or chr(nums[2])
                return Key(name, ctrl=ctrl, alt=alt, shift=shift)
            name = _CSI_TILDE.get(code)
            return Key(name, ctrl=ctrl, alt=alt, shift=shift) if name else None
        name = _CSI_LETTER.get(final)
        if name is None:
            return None
        if final == "Z":
            return Key("tab", shift=True, ctrl=ctrl, alt=alt)
        return Key(name, ctrl=ctrl, alt=alt, shift=shift)

    @staticmethod
    def _mouse_sgr(code: int, x: int, y: int, release: bool) -> Mouse:
        shift, alt, ctrl = bool(code & 4), bool(code & 8), bool(code & 16)
        base = code & ~(4 | 8 | 16)
        if base & 64:
            kind: Literal["press", "release", "drag", "wheel_up", "wheel_down", "move"] = (
                "wheel_up" if base & 1 == 0 else "wheel_down"
            )
            return Mouse(kind, x - 1, y - 1, 0, shift, alt, ctrl)
        button = base & 3
        if base & 32:
            return Mouse("move" if button == 3 else "drag", x - 1, y - 1, button, shift, alt, ctrl)
        return Mouse("release" if release else "press", x - 1, y - 1, button, shift, alt, ctrl)

    @staticmethod
    def _mouse_x10(code: int, x: int, y: int) -> Mouse:
        if code & 64:
            return Mouse("wheel_up" if code & 1 == 0 else "wheel_down", x - 1, y - 1)
        button = code & 3
        return Mouse("release" if button == 3 else "press", x - 1, y - 1, 0 if button == 3 else button)
