"""The real terminal: raw mode, the alternate screen, input reading, resize and suspend handling.

Everything that touches file descriptors, termios or signals lives here, so the rest of the TUI can be
driven headlessly in tests by substituting a buffer for the screen and a list for the input.
"""

from __future__ import annotations

import contextlib
import os
import select
import signal
import sys
import termios
import time
import tty
from collections.abc import Callable
from typing import Any

from frond.tui.style import RGB, parse_osc_color

ENTER_SEQ = (
    "\x1b[22;0t"  # push window title
    "\x1b[?1049h"  # alternate screen
    "\x1b[?7l"  # no autowrap: writing the last column must not scroll
    "\x1b[?25l"  # hide cursor while drawing
    "\x1b[?2004h"  # bracketed paste
    "\x1b[?1004h"  # focus in/out
)
MOUSE_ON = "\x1b[?1000h\x1b[?1006h"  # mouse buttons + wheel, SGR coordinates
KITTY_ON = "\x1b[>1u"  # kitty keyboard protocol: disambiguate escape codes
KITTY_OFF = "\x1b[<u"
EXIT_SEQ = (
    "\x1b[0m"
    "\x1b[?1004l"
    "\x1b[?1006l\x1b[?1000l"
    "\x1b[?2004l"
    "\x1b[0 q"  # default cursor shape
    "\x1b[?25h"
    "\x1b[?7h"
    "\x1b[?1049l"
    "\x1b[23;0t"  # pop window title
)


class Terminal:
    def __init__(self, fd_in: int | None = None, fd_out: int | None = None, *, mouse: bool = True) -> None:
        self.fd_in = sys.stdin.fileno() if fd_in is None else fd_in
        self.fd_out = sys.stdout.fileno() if fd_out is None else fd_out
        self._saved: list[Any] | None = None
        self._wake_r, self._wake_w = os.pipe()
        os.set_blocking(self._wake_w, False)
        os.set_blocking(self._wake_r, False)
        self.resized = False
        self.active = False
        self.kitty = os.environ.get("FROND_KITTY_KEYS", "1") != "0"
        self.mouse = mouse
        self.background: RGB | None = None
        self.leftover = b""
        self._handlers: dict[int, Any] = {}
        self.on_resume: Callable[[], None] | None = None

    # ── lifecycle ────────────────────────────────────────────────────────────

    @staticmethod
    def available() -> bool:
        return sys.stdin.isatty() and sys.stdout.isatty()

    def start(self, title: str | None = None) -> None:
        self._saved = termios.tcgetattr(self.fd_in)
        tty.setraw(self.fd_in, termios.TCSANOW)
        self.active = True
        self.write(ENTER_SEQ + (MOUSE_ON if self.mouse else "") + (KITTY_ON if self.kitty else ""))
        if title:
            self.set_title(title)
        self._install_signals()

    def stop(self) -> None:
        if not self.active:
            return
        self.active = False
        with contextlib.suppress(OSError):
            self.write((KITTY_OFF if self.kitty else "") + EXIT_SEQ)
        if self._saved is not None:
            with contextlib.suppress(termios.error):
                termios.tcsetattr(self.fd_in, termios.TCSADRAIN, self._saved)
        self._restore_signals()

    def suspend(self) -> None:
        """Ctrl+Z: give the terminal back, stop the process, and take over again on SIGCONT."""
        self.stop()
        os.kill(os.getpid(), signal.SIGTSTP)
        # Execution continues here after `fg`.
        self.start()
        self.resized = True
        if self.on_resume:
            self.on_resume()

    def _install_signals(self) -> None:
        def on_winch(signum: int, frame: Any) -> None:
            self.resized = True
            self.wake()

        def on_term(signum: int, frame: Any) -> None:
            self.stop()
            raise SystemExit(128 + signum)

        for sig, handler in ((signal.SIGWINCH, on_winch), (signal.SIGTERM, on_term), (signal.SIGHUP, on_term)):
            with contextlib.suppress(ValueError, OSError):
                self._handlers[sig] = signal.signal(sig, handler)

    def _restore_signals(self) -> None:
        for sig, handler in self._handlers.items():
            with contextlib.suppress(ValueError, OSError, TypeError):
                signal.signal(sig, handler)
        self._handlers.clear()

    # ── output ───────────────────────────────────────────────────────────────

    def write(self, data: str) -> None:
        raw = data.encode("utf-8", errors="replace")
        view = memoryview(raw)
        while view:
            try:
                written = os.write(self.fd_out, view)
            except BlockingIOError:
                select.select([], [self.fd_out], [], 0.1)
                continue
            except InterruptedError:
                continue
            view = view[written:]

    def set_title(self, title: str) -> None:
        clean = "".join(c for c in title if c.isprintable())[:120]
        self.write(f"\x1b]0;{clean}\x07")

    def size(self) -> tuple[int, int]:
        try:
            cols, rows = os.get_terminal_size(self.fd_out)
        except OSError:
            cols, rows = 80, 24
        return max(20, cols), max(8, rows)

    def bell(self) -> None:
        self.write("\x07")

    def copy_to_clipboard(self, text: str) -> None:
        """OSC 52: ask the terminal to put ``text`` on the system clipboard (works over SSH too)."""
        import base64

        self.write(f"\x1b]52;c;{base64.b64encode(text.encode()).decode()}\x07")

    # ── input ────────────────────────────────────────────────────────────────

    def wake(self) -> None:
        """Interrupt a blocking read() from another thread or a signal handler."""
        with contextlib.suppress(BlockingIOError, OSError):
            os.write(self._wake_w, b"x")

    def read(self, timeout: float | None) -> bytes:
        """Wait up to ``timeout`` seconds for input; returns b"" on timeout or wake-up."""
        if self.leftover:
            data, self.leftover = self.leftover, b""
            return data
        try:
            ready, _, _ = select.select([self.fd_in, self._wake_r], [], [], timeout)
        except InterruptedError:
            return b""
        if self._wake_r in ready:
            with contextlib.suppress(BlockingIOError, OSError):
                while os.read(self._wake_r, 4096):
                    pass
        if self.fd_in in ready:
            try:
                return os.read(self.fd_in, 65536)
            except (BlockingIOError, InterruptedError):
                return b""
        return b""

    def query_background(self, timeout: float = 0.25) -> RGB | None:
        """Ask the terminal for its background colour (OSC 11), using a DA1 query as a sentinel.

        Every terminal answers DA1, so if its reply arrives first the terminal ignored OSC 11 and we
        can stop waiting immediately. Bytes that are not part of either reply are kept as input.
        """
        self.write("\x1b]11;?\x1b\\\x1b[c")
        deadline = time.monotonic() + timeout
        data = b""
        while time.monotonic() < deadline:
            ready, _, _ = select.select([self.fd_in], [], [], max(0.0, deadline - time.monotonic()))
            if not ready:
                break
            data += os.read(self.fd_in, 4096)
            if b"\x1b[?" in data and data.rstrip().endswith(b"c"):
                break
        text = data.decode("utf-8", errors="replace")
        color = parse_osc_color(text) if "]11;" in text else None
        # Strip both replies; keep anything the user typed meanwhile.
        import re

        rest = re.sub(rb"\x1b\]11;[^\x07\x1b]*(\x07|\x1b\\)", b"", data)
        rest = re.sub(rb"\x1b\[\?[\d;]*c", b"", rest)
        self.leftover += rest
        self.background = color
        return color

    def close(self) -> None:
        self.stop()
        for fd in (self._wake_r, self._wake_w):
            with contextlib.suppress(OSError):
                os.close(fd)
