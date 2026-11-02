"""Drive the TUI without a terminal, and render frames as text or HTML.

This is frond's playground for UI work: script keystrokes against the real ``App`` (with the real agent and
a scripted model), then inspect frames as plain text in a test, or as colour-accurate HTML in a browser.

    uv run python -m frond.tui.headless --demo --type "add a flag" --wait --html out.html
"""

from __future__ import annotations

import argparse
import html
import sys
import time
from pathlib import Path

from frond.tui.app import App
from frond.tui.keys import Decoder, Key
from frond.tui.screen import Buffer
from frond.tui.style import RGB, Style, Theme, make_theme


class Harness:
    def __init__(self, app: App, width: int = 100, height: int = 32) -> None:
        self.app = app
        self.width = width
        self.height = height

    def send(self, data: bytes | str) -> None:
        """Feed raw terminal input (escape sequences included) through the real decoder."""
        raw = data.encode() if isinstance(data, str) else data
        decoder = Decoder()
        for event in [*decoder.feed(raw), *decoder.flush()]:
            self.app.on_input(event)

    def type(self, text: str) -> None:
        for ch in text:
            self.app.on_input(Key("enter") if ch == "\n" else Key(ch))

    def key(self, name: str, *, ctrl: bool = False, alt: bool = False, shift: bool = False) -> None:
        self.app.on_input(Key(name, ctrl=ctrl, alt=alt, shift=shift))

    def pump(self) -> int:
        return self.app.pump()

    def wait(self, predicate: object = None, timeout: float = 30.0) -> bool:
        """Pump agent events until ``predicate()`` holds (default: the turn and the queue are finished)."""
        deadline = time.monotonic() + timeout
        check = predicate if callable(predicate) else (lambda: not self.app.running and not self.app.queue)
        while time.monotonic() < deadline:
            self.pump()
            self.app.tick += 1
            if check():
                self.pump()
                return True
            time.sleep(0.01)
        return False

    def frame(self) -> Buffer:
        return self.app.draw(self.width, self.height)

    def text(self) -> str:
        return self.frame().dump()


def to_html(buf: Buffer, theme: Theme, *, title: str = "frond") -> str:
    """Render a frame as a standalone HTML page with the theme's colours (for screenshots)."""
    bg = theme.background
    fg: RGB = (222, 225, 232) if theme.dark else (36, 39, 46)

    def css(style: Style) -> str:
        parts = []
        f, b = style.fg or fg, style.bg
        if style.reverse:
            f, b = (b or bg), f
        parts.append(f"color:rgb{f}")
        if b is not None:
            parts.append(f"background:rgb{b}")
        if style.bold:
            parts.append("font-weight:700")
        if style.dim:
            parts.append("opacity:.6")
        if style.italic:
            parts.append("font-style:italic")
        decorations = [d for d, on in (("underline", style.underline), ("line-through", style.strike)) if on]
        if decorations:
            parts.append("text-decoration:" + " ".join(decorations))
        return ";".join(parts)

    rows = []
    for y in range(buf.height):
        cells = []
        run_style: Style | None = None
        run: list[str] = []
        for x in range(buf.width):
            ch = buf.chars[y][x]
            if ch == "":
                continue
            style = buf.styles[y][x]
            if buf.cursor == (x, y):
                style = style + Style(reverse=True)
            if style != run_style and run:
                cells.append(f'<span style="{css(run_style or Style())}">{html.escape("".join(run))}</span>')
                run = []
            run_style = style
            run.append(ch)
        if run:
            cells.append(f'<span style="{css(run_style or Style())}">{html.escape("".join(run))}</span>')
        rows.append(f'<div class="r">{"".join(cells) or " "}</div>')
    body = "".join(rows)
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
body{{margin:0;background:rgb{bg};}}
pre{{margin:0;padding:14px 16px;font:14px "JetBrains Mono","DejaVu Sans Mono","Menlo",monospace;
color:rgb{fg};background:rgb{bg};white-space:pre;letter-spacing:0;font-variant-ligatures:none}}
.r{{height:19px;line-height:19px}} .r span{{display:inline-block;height:19px;vertical-align:top}}
</style></head><body><pre>{body}</pre></body></html>"""


def _demo_app(width: int, height: int, theme: Theme) -> tuple[App, Harness]:
    from frond import demo
    from frond.agent.scripted import scripted_lm
    from frond.agent.session import Agent, AgentConfig
    from frond.workspace import Workspace

    root = demo.make_project()
    lm = scripted_lm(demo.make_engine(delay=0.0))
    ws = Workspace(root)
    app = App(ws, model="frond/scripted-demo", sub_model="frond/scripted-demo", theme=theme)
    agent = Agent(
        AgentConfig(model="frond/scripted-demo", sub_model="frond/scripted-demo", context_window=200_000),
        ws,
        app.emit,
        approver=app.approver,
        lm=lm,
        sub_lm=lm,
    )
    app.attach(agent)
    return app, Harness(app, width, height)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Render frond's TUI headlessly.")
    p.add_argument("--demo", action="store_true", help="use the scripted demo agent in a sample project")
    p.add_argument("--width", type=int, default=110)
    p.add_argument("--height", type=int, default=40)
    p.add_argument("--light", action="store_true")
    p.add_argument("--type", action="append", default=[], help="text to type, then press enter (repeatable)")
    p.add_argument("--keys", action="append", default=[], help="raw input to send, e.g. '\\x0f' for ctrl+o")
    p.add_argument("--wait", action="store_true", help="wait for the agent to finish before rendering")
    p.add_argument("--scroll", type=int, default=0, help="lines to scroll up before rendering")
    p.add_argument("--html", type=Path, help="write the frame as HTML to this path")
    args = p.parse_args(argv)
    theme = make_theme(dark=not args.light)
    if not args.demo:
        print("only --demo is supported from the command line", file=sys.stderr)
        return 2
    app, harness = _demo_app(args.width, args.height, theme)
    for text in args.type:
        harness.type(text + "\n")
        if args.wait:
            harness.wait()
    for raw in args.keys:
        harness.send(raw.encode().decode("unicode_escape").encode("latin-1"))
    harness.pump()
    app.scroll = args.scroll
    frame = harness.frame()
    if args.html:
        args.html.write_text(to_html(frame, app.theme))
    print(frame.dump())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
