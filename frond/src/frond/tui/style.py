"""Colours, text styles, SGR escape generation, and frond's two palettes.

Colours are RGB triples. The renderer emits 24-bit SGR when the terminal advertises truecolor and
otherwise maps to the nearest xterm-256 colour. Panel backgrounds are derived from the terminal's own
background (queried with OSC 11 at startup), so cards sit a shade off the user's theme instead of
fighting it.
"""

from __future__ import annotations

import functools
import os
from dataclasses import dataclass, replace
from typing import Literal

type RGB = tuple[int, int, int]
type ColorMode = Literal["truecolor", "256", "none"]


def hex_rgb(value: str) -> RGB:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def blend(a: RGB, b: RGB, t: float) -> RGB:
    return (round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t), round(a[2] + (b[2] - a[2]) * t))


def luminance(c: RGB) -> float:
    def channel(v: int) -> float:
        s = v / 255
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


@dataclass(frozen=True, slots=True)
class Style:
    fg: RGB | None = None
    bg: RGB | None = None
    bold: bool = False
    dim: bool = False
    italic: bool = False
    underline: bool = False
    reverse: bool = False
    strike: bool = False
    link: str | None = None

    def __add__(self, other: Style) -> Style:
        """Overlay ``other`` on this style: its colours win when set, attributes accumulate."""
        return Style(
            other.fg if other.fg is not None else self.fg,
            other.bg if other.bg is not None else self.bg,
            self.bold or other.bold,
            self.dim or other.dim,
            self.italic or other.italic,
            self.underline or other.underline,
            self.reverse or other.reverse,
            self.strike or other.strike,
            other.link if other.link is not None else self.link,
        )

    def with_bg(self, bg: RGB | None) -> Style:
        return replace(self, bg=bg)

    def with_fg(self, fg: RGB | None) -> Style:
        return replace(self, fg=fg)


PLAIN = Style()

_CUBE = (0, 95, 135, 175, 215, 255)


@functools.lru_cache(maxsize=4096)
def rgb_to_256(c: RGB) -> int:
    def nearest(v: int) -> int:
        return min(range(6), key=lambda i: abs(_CUBE[i] - v))

    r, g, b = (nearest(v) for v in c)
    cube = 16 + 36 * r + 6 * g + b
    cube_rgb = (_CUBE[r], _CUBE[g], _CUBE[b])
    gray_level = max(0, min(23, round((sum(c) / 3 - 8) / 10)))
    gray = 232 + gray_level
    level = 8 + 10 * gray_level
    gray_rgb = (level, level, level)

    def dist(x: RGB) -> int:
        return sum((x[i] - c[i]) ** 2 for i in range(3))

    return gray if dist(gray_rgb) < dist(cube_rgb) else cube


@functools.lru_cache(maxsize=8192)
def sgr(style: Style, mode: ColorMode) -> str:
    """The full SGR sequence for ``style``, starting from a reset."""
    codes = ["0"]
    if style.bold:
        codes.append("1")
    if style.dim:
        codes.append("2")
    if style.italic:
        codes.append("3")
    if style.underline:
        codes.append("4")
    if style.reverse:
        codes.append("7")
    if style.strike:
        codes.append("9")
    if mode != "none":
        for color, base in ((style.fg, "38"), (style.bg, "48")):
            if color is None:
                continue
            if mode == "truecolor":
                codes.append(f"{base};2;{color[0]};{color[1]};{color[2]}")
            else:
                codes.append(f"{base};5;{rgb_to_256(color)}")
    return f"\x1b[{';'.join(codes)}m"


def detect_color_mode(env: dict[str, str] | None = None) -> ColorMode:
    env = dict(os.environ) if env is None else env
    if env.get("NO_COLOR"):
        return "none"
    if env.get("COLORTERM", "").lower() in {"truecolor", "24bit"}:
        return "truecolor"
    program = env.get("TERM_PROGRAM", "")
    if program in {"iTerm.app", "WezTerm", "vscode", "ghostty", "Hyper", "Tabby", "WarpTerminal", "rio", "zed"}:
        return "truecolor"
    term = env.get("TERM", "")
    if any(t in term for t in ("kitty", "alacritty", "foot", "wezterm", "ghostty", "direct")):
        return "truecolor"
    if program == "Apple_Terminal" or "256" in term:
        return "256"
    return "256" if term and term != "dumb" else "none"


# ── themes ───────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Theme:
    name: str
    dark: bool
    background: RGB
    text: Style
    muted: Style
    faint: Style
    accent: Style
    accent_bold: Style
    info: Style
    warn: Style
    error: Style
    success: Style
    border: Style
    border_focus: Style
    panel: RGB
    panel_alt: RGB
    selection: Style
    user_bar: Style
    add: Style
    add_word: Style
    remove: Style
    remove_word: Style
    hunk: Style
    code_inline: Style
    link: Style
    heading: Style
    quote: Style
    syntax: dict[str, Style]
    meter_ok: RGB
    meter_mid: RGB
    meter_high: RGB
    meter_track: RGB

    def panel_style(self) -> Style:
        return Style(bg=self.panel)


def make_theme(dark: bool = True, background: RGB | None = None) -> Theme:
    if dark:
        bg = background or hex_rgb("#16171d")
        panel = blend(bg, (255, 255, 255), 0.045)
        panel_alt = blend(bg, (255, 255, 255), 0.085)
        accent = hex_rgb("#86c39b")  # fern
        info = hex_rgb("#8eaee0")
        warn = hex_rgb("#d9b46c")
        error = hex_rgb("#e48a8a")
        green = hex_rgb("#8fcf98")
        red = hex_rgb("#ea8f8f")
        muted = hex_rgb("#8c909b")
        faint = hex_rgb("#5d616c")
        border = hex_rgb("#3b3f49")
        syntax = {
            "keyword": Style(fg=hex_rgb("#c3a6ec")),
            "string": Style(fg=hex_rgb("#a8d39a")),
            "number": Style(fg=hex_rgb("#f0c27f")),
            "comment": Style(fg=hex_rgb("#6f7482"), italic=True),
            "function": Style(fg=hex_rgb("#8fbbe8")),
            "builtin": Style(fg=hex_rgb("#e8b4b0")),
            "decorator": Style(fg=hex_rgb("#f0c27f")),
            "type": Style(fg=hex_rgb("#8fd3d0")),
            "operator": Style(fg=hex_rgb("#a5abb8")),
            "constant": Style(fg=hex_rgb("#f0a07f")),
            "variable": Style(fg=hex_rgb("#d4d8e0")),
            "prompt": Style(fg=accent, bold=True),
        }
    else:
        bg = background or hex_rgb("#fbfbf9")
        panel = blend(bg, (0, 0, 0), 0.04)
        panel_alt = blend(bg, (0, 0, 0), 0.075)
        accent = hex_rgb("#2f7d4f")
        info = hex_rgb("#3a62a8")
        warn = hex_rgb("#9a6b13")
        error = hex_rgb("#b23b3b")
        green = hex_rgb("#2c7a3f")
        red = hex_rgb("#b33a3a")
        muted = hex_rgb("#6a6e78")
        faint = hex_rgb("#9a9ea8")
        border = hex_rgb("#cfd2d8")
        syntax = {
            "keyword": Style(fg=hex_rgb("#7b3fb3")),
            "string": Style(fg=hex_rgb("#3d7a2a")),
            "number": Style(fg=hex_rgb("#a35b00")),
            "comment": Style(fg=hex_rgb("#8a8f99"), italic=True),
            "function": Style(fg=hex_rgb("#2a5db0")),
            "builtin": Style(fg=hex_rgb("#a33f5c")),
            "decorator": Style(fg=hex_rgb("#a35b00")),
            "type": Style(fg=hex_rgb("#13777a")),
            "operator": Style(fg=hex_rgb("#5a5f6a")),
            "constant": Style(fg=hex_rgb("#b24f20")),
            "variable": Style(fg=hex_rgb("#2b2f36")),
            "prompt": Style(fg=accent, bold=True),
        }
    return Theme(
        name="dark" if dark else "light",
        dark=dark,
        background=bg,
        text=Style(),
        muted=Style(fg=muted),
        faint=Style(fg=faint),
        accent=Style(fg=accent),
        accent_bold=Style(fg=accent, bold=True),
        info=Style(fg=info),
        warn=Style(fg=warn),
        error=Style(fg=error),
        success=Style(fg=green),
        border=Style(fg=border),
        border_focus=Style(fg=blend(border, accent, 0.55)),
        panel=panel,
        panel_alt=panel_alt,
        selection=Style(bg=blend(panel, accent, 0.22)),
        user_bar=Style(fg=info),
        add=Style(fg=green, bg=blend(panel, green, 0.10)),
        add_word=Style(fg=green, bg=blend(panel, green, 0.24)),
        remove=Style(fg=red, bg=blend(panel, red, 0.10)),
        remove_word=Style(fg=red, bg=blend(panel, red, 0.24)),
        hunk=Style(fg=faint),
        code_inline=Style(fg=hex_rgb("#e3c08f") if dark else hex_rgb("#8a4f0b")),
        link=Style(fg=info, underline=True),
        heading=Style(fg=accent, bold=True),
        quote=Style(fg=muted, italic=True),
        syntax=syntax,
        meter_ok=accent,
        meter_mid=warn,
        meter_high=error,
        meter_track=border,
    )


def parse_osc_color(reply: str) -> RGB | None:
    """Parse an OSC 10/11 colour reply such as ``rgb:1e1e/1e1e/2020``."""
    marker = reply.find("rgb:")
    if marker == -1:
        return None
    body = reply[marker + 4 :].split("\x07")[0].split("\x1b")[0]
    parts = body.split("/")
    if len(parts) != 3:
        return None
    try:
        values = [int(p, 16) / (16 ** len(p) - 1) for p in parts]
    except ValueError:
        return None
    r, g, b = (round(v * 255) for v in values)
    return (r, g, b)
