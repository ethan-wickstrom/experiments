"""The REPL worker: runs the agent's Python in a persistent namespace, in its own process.

Standard library only; started as ``python -I -B _worker.py`` by ``frond.agent.repl``. It speaks
newline-delimited JSON with the host over stdin and a private duplicate of stdout:

  host → worker   execute | tool_result | tool_error | fork | shutdown
  worker → host   ready | stdout | tool_request | done | forked | fork_failed

Design points:

* User code runs on the main thread, so the host's SIGINT becomes a KeyboardInterrupt exactly where the
  code is, and the namespace survives the interruption.
* Host tools appear as ordinary functions. Calls block on a per-request queue; a reader thread routes
  replies, so code may call tools from several threads at once.
* A PEP 578 audit hook refuses subprocesses and file writes outside temp directories while user code
  runs. Not a security boundary (ctypes can evade it), but it keeps a well-meaning model on the tools,
  where every command and diff is visible to the user.
* Between steps the worker can fork (ledger B6): the host passes a new socket over the UNIX socket named by
  FROND_FORK_FD (SCM_RIGHTS), and the child, a copy of the namespace in its own session, speaks the same
  protocol on it. The child inherits the sandbox: namespaces and Landlock survive fork.
"""

from __future__ import annotations

import ast
import builtins
import inspect
import io
import itertools
import json
import os
import queue
import signal
import socket
import sys
import tempfile
import threading
import time
import traceback
import types
import warnings
from typing import Any

PROTOCOL = os.fdopen(os.dup(1), "w", encoding="utf-8", buffering=1)
os.set_inheritable(PROTOCOL.fileno(), False)
_fork_fd = int(os.environ.pop("FROND_FORK_FD", "-1"))  # where the host sends a forked worker's channel
FORKS: socket.socket | None = socket.socket(fileno=_fork_fd) if _fork_fd >= 0 else None
_devnull = os.open(os.devnull, os.O_WRONLY)
os.dup2(_devnull, 1)
os.dup2(_devnull, 2)
os.close(_devnull)

MAX_CAPTURE = 2_000_000
STREAM_INTERVAL = 0.05
REPR_LIMIT = 4000
MAX_NAMES = 40
RESERVED = {"SUBMIT", "FORK", "ToolError"}
MAX_BRANCH_STEPS = 12
_send_lock = threading.Lock()


def send(message: dict[str, Any]) -> None:
    line = json.dumps(message, separators=(",", ":"), default=repr)
    with _send_lock:
        PROTOCOL.write(line + "\n")
        PROTOCOL.flush()


class Submission(BaseException):
    def __init__(self, value: Any) -> None:
        super().__init__()
        self.value = value


class Branching(BaseException):
    """Raised by FORK: the step ends here, and the host explores the options (ledger B7)."""

    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__()
        self.value = value


class ToolError(Exception):
    """Raised in user code when a host tool fails for a reason the code can handle or report."""


# ── friendly result types ────────────────────────────────────────────────────


class AttrDict(dict):
    """A dict whose keys are also attributes: ``r.output`` as well as ``r["output"]``."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None


class CommandResult(AttrDict):
    def __str__(self) -> str:
        status = self.get("status", "")
        extra = "" if status in {"ok", "failed"} else f", {status}"
        head = f"$ {self.get('command', '')}  [exit {self.get('exit_code')}, {self.get('duration')}s{extra}]"
        out = self.get("output", "")
        return head + ("\n" + out if out else "\n(no output)")

    __repr__ = __str__


class JobHandle(AttrDict):
    def __str__(self) -> str:
        state = "running" if self.get("running") else f"exited ({self.get('exit_code')})"
        out = self.get("output", "")
        return f"job {self.get('job')} (pid {self.get('pid')}) {state}; log: {self.get('log')}" + (
            "\n" + out if out else ""
        )

    __repr__ = __str__


class Matches(list):
    """grep() results: a list of AttrDict(path, line, text, before, after) with a readable str()."""

    query = ""
    truncated = False
    files = 0

    def __str__(self) -> str:
        if not self:
            return f"no matches for {self.query!r}"
        out: list[str] = []
        current = None
        for m in self:
            if m.path != current:
                current = m.path
                out.append(m.path)
            for n, text in m.get("before", []):
                out.append(f"  {n}- {text}")
            out.append(f"  {m.line}: {m.text}")
            for n, text in m.get("after", []):
                out.append(f"  {n}- {text}")
        tail = f"({len(self)} matches in {self.files} files" + (
            ", truncated — narrow the search)" if self.truncated else ")"
        )
        return "\n".join([*out, tail])

    __repr__ = __str__


def rehydrate(value: Any) -> Any:
    if isinstance(value, dict):
        kind = value.get("__frond__")
        if kind == "command":
            return CommandResult({k: v for k, v in value.items() if k != "__frond__"})
        if kind == "job":
            return JobHandle({k: v for k, v in value.items() if k != "__frond__"})
        if kind == "matches":
            matches = Matches(AttrDict(m) for m in value.get("items", []))
            matches.query = value.get("query", "")
            matches.truncated = bool(value.get("truncated"))
            matches.files = int(value.get("files", 0))
            return matches
        return AttrDict({k: rehydrate(v) for k, v in value.items()})
    if isinstance(value, list):
        return [rehydrate(v) for v in value]
    return value


# ── output capture ───────────────────────────────────────────────────────────


class Capture(io.TextIOBase):
    """Collects everything written while user code runs and streams it to the host in small batches."""

    def __init__(self) -> None:
        self.parts: list[str] = []
        self.size = 0
        self.pending: list[str] = []
        self.last = time.monotonic()
        self.lock = threading.Lock()

    def writable(self) -> bool:
        return True

    def write(self, s: str) -> int:
        if not isinstance(s, str):
            s = str(s)
        with self.lock:
            if self.size < MAX_CAPTURE:
                self.parts.append(s)
                self.size += len(s)
            self.pending.append(s)
            if time.monotonic() - self.last > STREAM_INTERVAL or sum(map(len, self.pending)) > 4096:
                self._flush_locked()
        return len(s)

    def _flush_locked(self) -> None:
        if self.pending:
            send({"type": "stdout", "text": "".join(self.pending)})
            self.pending = []
        self.last = time.monotonic()

    def flush(self) -> None:
        with self.lock:
            self._flush_locked()

    def value(self) -> str:
        text = "".join(self.parts)
        if self.size >= MAX_CAPTURE:
            text += "\n… (output capture limit reached)"
        return text


# ── policy ───────────────────────────────────────────────────────────────────

_active = threading.Event()  # set while user code runs
_ORIGINAL_STREAMS = (sys.stdout, sys.stderr)
# The OS sandbox this worker runs in (set by _sandbox.py), or "". Confined, TMPDIR is the one writable place, and
# commands outside the sandbox can read what is written there.
_SANDBOX = os.environ.get("FROND_SANDBOXED", "")
_SCRATCH = os.path.realpath(tempfile.gettempdir())
_ALLOWED_WRITE_DIRS = (
    (_SCRATCH, os.path.realpath(os.devnull))
    if _SANDBOX
    else tuple({_SCRATCH, "/tmp", "/private/tmp", "/var/folders", os.path.realpath(os.devnull)})
)
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
_SUBPROCESS_EVENTS = {
    "subprocess.Popen",
    "os.system",
    "os.exec",
    "os.spawn",
    "os.posix_spawn",
    "os.fork",
    "os.forkpty",
    "pty.spawn",
}
_PATH_EVENTS = {
    "os.remove",
    "os.rename",
    "os.rmdir",
    "shutil.rmtree",
    "os.truncate",
    "os.link",
    "os.symlink",
    "os.chmod",
    "os.chown",
    "shutil.move",
    "shutil.copytree",
}
# Network access from the model's code: sockets for the internet (TCP and UDP), name lookups (which can carry data
# out over DNS), urllib, and connections to local services through UNIX socket files (docker, ssh-agent). Every
# request the agent makes should be a command the user can see. Sockets between threads (socketpair) still work.
_NETWORK_FAMILIES = {socket.AF_INET, socket.AF_INET6}
_LOOKUP_EVENTS = {"socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr", "socket.getnameinfo"}
NO_NETWORK = "frond: the REPL has no network access; use sh(...) for anything that needs it, so the user sees it"


def _writable_path(path: Any) -> bool:
    if isinstance(path, int):
        return True
    try:
        real = os.path.realpath(os.fsdecode(path))
    except (TypeError, ValueError):
        return True
    return any(real == d or real.startswith(d.rstrip("/") + "/") for d in _ALLOWED_WRITE_DIRS)


def _audit(event: str, args: tuple[Any, ...]) -> None:
    if not _active.is_set():
        return
    if event in _SUBPROCESS_EVENTS:
        raise PermissionError("frond: start commands with sh(...), not from Python, so the user can see them")
    if event == "socket.__new__" and len(args) > 1 and args[1] in _NETWORK_FAMILIES:
        raise PermissionError(NO_NETWORK)
    if event in _LOOKUP_EVENTS or event == "urllib.Request":
        raise PermissionError(NO_NETWORK)
    if event == "socket.connect" and len(args) > 1 and isinstance(args[1], (str, bytes)):
        raise PermissionError(NO_NETWORK)  # a UNIX socket: a local service such as docker, D-Bus or ssh-agent
    if event == "open":
        path, mode, flags = [*args, None, None, None][:3]
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int) and flags & _WRITE_FLAGS
        )
        if writing and not _writable_path(path):
            raise PermissionError(
                "frond: write files with write()/edit()/patch() so the user sees a diff "
                f"(scratch files under {_SCRATCH} are fine)"
            )
    elif event in _PATH_EVENTS and args and not _writable_path(args[0]):
        raise PermissionError(f"frond: {event} is blocked in the REPL; use the delete()/move() tools")


# ── the session ──────────────────────────────────────────────────────────────


class Session:
    def __init__(self, inp: Any = None) -> None:
        self.inp = inp if inp is not None else sys.stdin
        self.ids = itertools.count(1)
        self.pending: dict[int, queue.Queue[dict[str, Any]]] = {}
        self.pending_lock = threading.Lock()
        self.commands: queue.Queue[dict[str, Any] | None] = queue.Queue()
        self.namespace: dict[str, Any] = {"__name__": "__repl__", "__builtins__": builtins}
        self.tool_names: set[str] = set()
        self.output_fields: list[dict[str, Any]] | None = None
        self.max_branches = 1  # FORK exists when the host allows two or more branches
        self.executing = False
        threading.Thread(target=self._read, name="frond-worker-reader", daemon=True).start()
        self.own_threads = set(threading.enumerate())  # the worker's, as against those the agent's code starts (F24)

    def _read(self) -> None:
        for line in self.inp:
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = message.get("type")
            if kind in {"tool_result", "tool_error"}:
                with self.pending_lock:
                    box = self.pending.get(message.get("id"))
                if box is not None:
                    box.put(message)
            else:
                self.commands.put(message)
        self.commands.put(None)
        with self.pending_lock:
            boxes = list(self.pending.values())
        for box in boxes:
            box.put({"type": "tool_error", "error_type": "EOFError", "message": "host connection closed"})

    def fork(self) -> dict[str, Any] | None:
        """Copy this worker, namespace and all, into a new process with its own channel to the host.

        In the original, returns the reply for the host. In the copy, it has already said "ready" on its new
        channel and returns None. Only the original forks: a copy has no channel for receiving another.
        """
        global PROTOCOL, FORKS, _send_lock
        if FORKS is None:
            return {"type": "fork_failed", "error": "this worker has no fork channel"}
        _, fds, _, _ = socket.recv_fds(FORKS, 1, 1)
        if not fds:
            return {"type": "fork_failed", "error": "no channel arrived"}
        # Threads the agent's code left running would not come along, and a lock one of them holds at the fork
        # would stay held in every copy, which then hangs on it (F24): refuse, and say which threads.
        threads = [t.name for t in threading.enumerate() if t not in self.own_threads and t.is_alive()]  # by identity
        if threads:
            os.close(fds[0])
            return {
                "type": "fork_failed",
                "error": f"threads your code started are still running ({', '.join(threads)}); a copy would not "
                "have them, and a lock one holds would stay held in it. Stop them, then FORK",
            }
        original = os.getpid()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)  # forking with idle daemon threads; see below
                pid = os.fork()
        except OSError:
            os.close(fds[0])  # F25: the channel for a copy that never existed
            raise
        if pid:
            os.close(fds[0])
            return {"type": "forked", "pid": pid}
        # The copy. Only this thread exists here; the reader thread did not come along, and the locks it may
        # hold (stdin's buffer) are never touched again: inherited descriptors are replaced at the OS level.
        os.setsid()  # its own process group, so the host can interrupt and kill it alone
        _die_with_parent(original)  # F22: a copy outlives no original, even one whose host was killed
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)
        devnull = os.open(os.devnull, os.O_RDWR)
        os.dup2(devnull, 0)  # the original's input
        os.dup2(devnull, PROTOCOL.fileno())  # the original's line to the host
        os.close(devnull)
        FORKS.close()
        FORKS = None
        own = tempfile.mkdtemp(prefix="fork-", dir=_SCRATCH)  # scratch files of its own, under the shared one
        os.environ["TMPDIR"] = tempfile.tempdir = own
        channel = socket.socket(fileno=fds[0])
        PROTOCOL = channel.makefile("w", encoding="utf-8", buffering=1)
        _send_lock = threading.Lock()
        self.inp = channel.makefile("r", encoding="utf-8")
        self.ids = itertools.count(1)
        self.pending, self.pending_lock, self.commands = {}, threading.Lock(), queue.Queue()
        threading.Thread(target=self._read, name="frond-worker-reader", daemon=True).start()
        # the host removes this directory when it shuts the copy down, however the copy ends (F23)
        send(
            {"type": "ready", "pid": os.getpid(), "python": sys.version.split()[0], "sandbox": _SANDBOX, "scratch": own}
        )
        return None

    def call_tool(self, name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        request_id = next(self.ids)
        box: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=1)
        with self.pending_lock:
            self.pending[request_id] = box
        try:
            send({"type": "tool_request", "id": request_id, "name": name, "args": list(args), "kwargs": kwargs})
            reply = box.get()
        finally:
            with self.pending_lock:
                self.pending.pop(request_id, None)
        if reply.get("type") == "tool_error":
            exc_type = getattr(builtins, str(reply.get("error_type")), None)
            message = str(reply.get("message", ""))
            if isinstance(exc_type, type) and issubclass(exc_type, Exception) and exc_type.__module__ == "builtins":
                raise exc_type(message)
            raise ToolError(message)
        return rehydrate(reply.get("value"))

    def configure(
        self, tools: dict[str, dict[str, str]], output_fields: list[dict[str, Any]] | None, max_branches: int = 1
    ) -> None:
        for name in self.tool_names - set(tools):
            self.namespace.pop(name, None)
        self.tool_names = set(tools)
        self.output_fields = output_fields
        for name, spec in tools.items():
            self.namespace[name] = make_stub(self, name, spec.get("doc", ""), spec.get("signature", ""))
        self.namespace["SUBMIT"] = self.submit
        self.namespace["ToolError"] = ToolError
        self.max_branches = max_branches
        if max_branches > 1:
            self.namespace["FORK"] = self.branch
        else:
            self.namespace.pop("FORK", None)

    def branch(self, options: list[str], check: str | None = None, steps: int = 8) -> None:
        """FORK: explore ``options`` in copies of the workspace and REPL; the host keeps the one ``check`` passes."""
        if not isinstance(options, (list, tuple)) or not all(isinstance(o, str) and o.strip() for o in options):
            raise TypeError("FORK takes options: a list of non-empty strings, one per approach to try")
        if not 2 <= len(options) <= self.max_branches:
            raise ValueError(f"FORK takes 2 to {self.max_branches} options; got {len(options)}")
        if check is not None and not (isinstance(check, str) and check.strip()):
            raise TypeError("check must be a shell command (a string) whose exit code 0 means success")
        if not isinstance(steps, int) or not 1 <= steps <= MAX_BRANCH_STEPS:
            raise ValueError(f"steps must be an integer from 1 to {MAX_BRANCH_STEPS}")
        raise Branching({"options": [o.strip() for o in options], "check": check, "steps": steps})

    def submit(self, *args: Any, **kwargs: Any) -> None:
        fields = [f["name"] for f in self.output_fields or []]
        if not fields:
            if len(args) != 1 or kwargs:
                raise TypeError("SUBMIT takes exactly one value")
            raise Submission({"output": args[0]})
        if args and kwargs:
            raise TypeError("SUBMIT accepts positional or keyword arguments, not both")
        values = dict(zip(fields, args, strict=False)) if args else dict(kwargs)
        if len(args) > len(fields) or set(values) != set(fields):
            raise TypeError(f"SUBMIT expects {', '.join(fields)}; got {', '.join(values) or 'nothing'}")
        raise Submission(values)

    def execute(self, request: dict[str, Any]) -> dict[str, Any]:
        self.configure(request.get("tools") or {}, request.get("output_fields"), int(request.get("branches") or 1))
        for key, value in (request.get("variables") or {}).items():
            if key in self.tool_names or key in {"SUBMIT", "FORK", "__builtins__"}:
                continue
            self.namespace[key] = value
        code = request.get("code", "")
        capture = Capture()
        result: dict[str, Any] = {"type": "done", "status": "ok"}
        threads_before = set(threading.enumerate())
        sys.stdout = sys.stderr = capture
        try:
            tree = ast.parse(code, filename="<repl>", mode="exec")
        except SyntaxError as exc:
            sys.stdout, sys.stderr = _ORIGINAL_STREAMS
            detail = "".join(traceback.format_exception_only(type(exc), exc)).strip()
            return {"type": "done", "status": "syntax", "error": detail, "stdout": ""}
        last_expr = None
        if tree.body and isinstance(tree.body[-1], ast.Expr):
            last_expr = ast.Expression(tree.body.pop().value)
        self.executing = True
        _active.set()
        try:
            exec(compile(tree, "<repl>", "exec", dont_inherit=True), self.namespace)
            if last_expr is not None:
                value = eval(compile(last_expr, "<repl>", "eval", dont_inherit=True), self.namespace)
                if value is not None:
                    text = repr(value)
                    if len(text) > REPR_LIMIT:
                        text = text[:REPR_LIMIT] + f"… [{len(text) - REPR_LIMIT:,} more chars; print a slice]"
                    print(text)
        except Submission as sub:
            result = {"type": "done", "status": "final", "value": sub.value}
        except Branching as fork:
            result = {"type": "done", "status": "fork", "value": fork.value}
        except KeyboardInterrupt:
            result = {
                "type": "done",
                "status": "interrupted",
                "error": "KeyboardInterrupt: execution interrupted",
            }
        except SystemExit as exc:
            result = {
                "type": "done",
                "status": "error",
                "error": f"SystemExit({exc.code!r}): exiting is not allowed; the REPL persists between steps",
            }
        except BaseException as exc:
            result = {"type": "done", "status": "error", "error": format_user_traceback(exc)}
        finally:
            _active.clear()
            self.executing = False
            sys.stdout, sys.stderr = _ORIGINAL_STREAMS
            capture.flush()
        result["stdout"] = capture.value()
        result["names"] = self.describe_names(set(request.get("variables") or {}))
        leaked = [t.name for t in set(threading.enumerate()) - threads_before if t.is_alive() and not t.daemon]
        if leaked:
            result["warning"] = f"code left threads running: {', '.join(leaked)}; join them before a step ends"
        return result

    def describe_names(self, inputs: set[str]) -> list[str]:
        """One short line per name the code has defined: what later steps (and turns) can still use."""
        lines: list[str] = []
        names = [
            name
            for name, value in self.namespace.items()
            if not name.startswith("_")
            and name not in inputs
            and name not in self.tool_names
            and name not in RESERVED
            and not isinstance(value, types.ModuleType)
        ]
        lines.extend(describe(name, self.namespace[name]) for name in names[:MAX_NAMES])
        if len(names) > MAX_NAMES:
            lines.append(f"… and {len(names) - MAX_NAMES} more (print(dir()) lists them)")
        return lines


def describe(name: str, value: Any) -> str:
    kind = type(value).__name__
    try:
        if value is None or isinstance(value, (bool, int, float, complex)):
            return f"{name} = {value!r}"
        if isinstance(value, str):
            return f"{name} = {value!r}" if len(value) <= 60 else f"{name}: str, {len(value):,} chars"
        if inspect.isclass(value):
            return f"{name}: class"
        if inspect.isfunction(value) or inspect.ismethod(value):
            return f"{name}{inspect.signature(value)}: function"
        shape = getattr(value, "shape", None)
        if isinstance(shape, tuple):
            return f"{name}: {kind}, shape {shape}"
        if isinstance(value, dict):
            keys = ", ".join(repr(k) for k in list(value)[:4])
            return f"{name}: dict, {len(value):,} keys ({keys}{', …' if len(value) > 4 else ''})"
        if hasattr(value, "__len__"):
            return f"{name}: {kind}, {len(value):,} items"
    except Exception:  # a value whose len() or signature fails still gets a line
        pass
    return f"{name}: {kind}"


def make_stub(session: Session, name: str, doc: str, signature: str) -> Any:
    """A namespace function that forwards to the host tool ``name`` and carries its real signature."""

    def stub(*args: Any, **kwargs: Any) -> Any:
        return session.call_tool(name, args, kwargs)

    stub.__name__ = stub.__qualname__ = name
    stub.__doc__ = doc or None
    if signature:
        import inspect
        import typing

        for prelude in ("", "from __future__ import annotations\n"):
            scratch: dict[str, Any] = {"Any": typing.Any}
            try:
                exec(
                    compile(f"{prelude}def _sig{signature}: pass", "<sig>", "exec", dont_inherit=True),
                    scratch,
                )
                setattr(stub, "__signature__", inspect.signature(scratch["_sig"]))  # noqa: B010
                break
            except Exception:
                continue
    return stub


def format_user_traceback(exc: BaseException) -> str:
    """Traceback limited to the agent's own code (frames from <repl>), which is all the model can fix."""
    frames = [f for f in traceback.extract_tb(exc.__traceback__) if f.filename == "<repl>"]
    lines = []
    if frames:
        lines.append("Traceback (most recent call last):\n")
        lines += traceback.format_list(frames[-6:])
    lines += traceback.format_exception_only(type(exc), exc)
    return "".join(lines).rstrip()


def _on_sigint(signum: int, frame: Any) -> None:
    if _active.is_set():
        raise KeyboardInterrupt


def _reap(signum: int, frame: Any) -> None:
    """Collect forked copies that ended, so none lingers as a zombie the host would think alive."""
    while True:
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return
        if pid == 0:
            return


def main() -> None:
    signal.signal(signal.SIGINT, _on_sigint)
    signal.signal(signal.SIGCHLD, _reap)  # user code cannot start processes here, so every child is a fork
    setattr(builtins, "input", _no_input)  # noqa: B010 - replacing a builtin on purpose
    if os.environ.get("FROND_REPL_POLICY", "strict") != "off":
        sys.addaudithook(_audit)
    session = Session()
    send({"type": "ready", "pid": os.getpid(), "python": sys.version.split()[0], "sandbox": _SANDBOX})
    while True:
        request = session.commands.get()
        if request is None or request.get("type") == "shutdown":
            return
        if request.get("type") == "execute":
            try:
                send(session.execute(request))
            except BaseException as exc:  # never let the loop die on a protocol hiccup
                send({"type": "done", "status": "error", "error": f"worker failure: {exc!r}", "stdout": ""})
        elif request.get("type") == "fork":
            try:
                reply = session.fork()
            except OSError as exc:
                reply = {"type": "fork_failed", "error": repr(exc)}
            if reply is not None:  # None: this is the copy, already announced on its own channel
                send(reply)


def _die_with_parent(parent: int) -> None:
    """Have Linux kill this process when its parent, the original worker, exits (PR_SET_PDEATHSIG). Elsewhere, or
    when it cannot be set, the host's shutdown of the original still shuts its copies down."""
    if not sys.platform.startswith("linux"):
        return
    try:
        import ctypes

        libc = ctypes.CDLL(None, use_errno=True)
        libc.prctl(1, signal.SIGKILL, 0, 0, 0)  # PR_SET_PDEATHSIG
        if os.getppid() != parent:  # the parent was gone before the call took effect
            os._exit(0)
    except (OSError, AttributeError):
        pass


def _no_input(prompt: object = "", /) -> str:
    raise EOFError("input() is unavailable: nobody is typing into this REPL. Use the variables you were given.")


if __name__ == "__main__":
    main()
