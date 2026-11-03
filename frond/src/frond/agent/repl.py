"""Host side of the REPL: a dspy ``CodeInterpreter`` backed by a persistent CPython worker process.

Compared with ``dspy.LocalInterpreter`` this adds what an interactive agent needs: live stdout, stopping a
running step with SIGINT without losing the namespace, per-step timeouts, positional tool arguments, keeping
printed output when code fails, and one session that persists across conversation turns.
"""

from __future__ import annotations

import contextlib
import contextvars
import inspect
import json
import os
import queue
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import IO, Any, Protocol

import dspy
from dspy.primitives.code_interpreter import CodeExecutionError, CodeInterpreterError, FinalOutput

from frond.agent.control import TurnCancelled, TurnControl
from frond.agent.shell import sandbox_status, sandboxed_argv, scrubbed_env
from frond.agent.tools import display_signature

WORKER = Path(__file__).with_name("_worker.py")
EXECUTION_INSTRUCTIONS = (
    "Code runs in a persistent CPython process whose working directory is the workspace root. Variables, "
    "imports and functions persist between steps and across conversation turns. The tools are ordinary global "
    "functions (call them positionally or by keyword). Subprocesses and file writes from Python are blocked: "
    "use sh() and write()/edit()/patch() so the user sees every command and diff. Use threads (e.g. "
    "concurrent.futures.ThreadPoolExecutor in a with-block) for parallel tool calls."
)

type OutputSink = Callable[[str], None]
_IDLE: dict[str, Any] = {"type": "idle"}
# FROND_SANDBOX value -> why a confined worker would not start here, so later workers skip straight to the fallback
_confine_failures: dict[str, str] = {}


class _Process(Protocol):
    """What a session needs of its worker process: a ``subprocess.Popen``, or a ``_Forked``."""

    pid: int
    stdin: IO[str] | None
    stdout: IO[str] | None
    stderr: IO[str] | None

    def poll(self) -> int | None: ...
    def wait(self, timeout: float | None = None) -> int: ...


class _Forked:
    """A worker that another worker forked (ledger B6). frond is not its parent, so this stands in for Popen: the
    protocol runs over a socket, and liveness comes from the pid (the parent worker reaps it)."""

    def __init__(self, pid: int, channel: socket.socket) -> None:
        self.pid = pid
        self.channel = channel
        self.stdin: IO[str] | None = channel.makefile("w", encoding="utf-8", newline="\n")
        self.stdout: IO[str] | None = channel.makefile("r", encoding="utf-8", newline="\n")
        self.stderr: IO[str] | None = None
        self.returncode: int | None = None

    def poll(self) -> int | None:
        if self.returncode is None:
            try:
                os.kill(self.pid, 0)
            except ProcessLookupError:
                self.returncode = -signal.SIGKILL
            except PermissionError:
                pass
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        deadline = None if timeout is None else time.monotonic() + timeout
        while (code := self.poll()) is None:
            if deadline is not None and time.monotonic() > deadline:
                raise subprocess.TimeoutExpired(f"forked worker {self.pid}", timeout or 0)
            time.sleep(0.02)
        return code


def _call_tool(fn: Callable[..., Any], args: list[Any], kwargs: dict[str, Any]) -> Any:
    """Call ``fn`` with positional args mapped onto parameter names (dspy's tool wrappers take kwargs only)."""
    if not args:
        return fn(**kwargs)
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return fn(*args, **kwargs)
    if any(p.kind is inspect.Parameter.VAR_POSITIONAL for p in sig.parameters.values()):
        return fn(*args, **kwargs)
    bound = sig.bind(*args, **kwargs)
    call: dict[str, Any] = {}
    for name, value in bound.arguments.items():
        if sig.parameters[name].kind is inspect.Parameter.VAR_KEYWORD:
            call.update(value)
        else:
            call[name] = value
    return fn(**call)


def _signature_text(fn: Callable[..., Any]) -> str:
    sig = display_signature(fn)
    return "" if sig == "(...)" else sig


class ReplSession:
    """One worker process. Implements ``start``/``execute``/``shutdown``/``tools`` (dspy's CodeInterpreter)."""

    def __init__(
        self,
        cwd: Path,
        *,
        control: TurnControl | None = None,
        on_output: OutputSink | None = None,
        timeout: float = 900.0,
        policy: str = "strict",
        sandbox: bool = True,
    ) -> None:
        self.cwd = cwd
        self.control = control or TurnControl()
        self.on_output = on_output
        self.timeout = timeout
        self.policy = policy
        self.sandbox = sandbox
        self.confinement = ""  # the OS sandbox the worker runs in ("namespaces", "landlock", "seatbelt"), or ""
        self.unconfined_reason = ""  # why it runs without one
        self._scratch: str | None = None  # the worker's TMPDIR when confined: writable, and readable by commands
        self._tools: dict[str, Callable[..., Any]] = {}
        self.output_fields: list[dict[str, Any]] | None = None
        self._proc: _Process | None = None
        self._forks: socket.socket | None = None  # where this session sends a forked worker its channel (B6)
        self._inbox: queue.Queue[dict[str, Any] | None] = queue.Queue()
        self._send_lock = threading.Lock()
        self._exec_lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=16, thread_name_prefix="frond-tool")
        self._closed = False
        self.restarts = 0
        self.names: list[str] = []  # what the code has defined, as of the last step (see _worker.describe_names)

    @property
    def tools(self) -> dict[str, Callable[..., Any]]:
        return self._tools

    @property
    def pid(self) -> int | None:
        return self._proc.pid if self._proc else None

    # ── lifecycle ────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the worker: confined by the OS sandbox where one works here, and never holding credentials.

        The model's code needs neither the network nor writes outside its temp directory, because everything it
        changes goes through the host's tools, which ask, journal and show. The sandbox makes that hold even for
        code that gets around the audit hook (with ctypes, say), and keeps an injected instruction from sending
        anything out. Where no sandbox works, the worker still runs, without credentials and under the hook.
        """
        if self._closed:
            raise CodeInterpreterError("REPL session has been shut down")
        if self._proc is not None and self._proc.poll() is None:
            return
        env = {**scrubbed_env(os.environ), "FROND_REPL_POLICY": self.policy, "PYTHONIOENCODING": "utf-8"}
        argv = [sys.executable, "-I", "-B", "-u", str(WORKER)]
        if self._forks is not None:
            self._forks.close()
        self._forks, worker_end = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        env["FROND_FORK_FD"] = str(worker_end.fileno())
        try:
            self._start_worker(argv, env, worker_end)
        finally:
            worker_end.close()  # the worker holds its own copy

    def _start_worker(self, argv: list[str], env: dict[str, str], worker_end: socket.socket) -> None:
        if self.sandbox and self.policy != "off":
            key = os.environ.get("FROND_SANDBOX", "")
            available, why = sandbox_status(self.cwd)
            if available and key not in _confine_failures:
                if self._scratch is None:
                    self._scratch = tempfile.mkdtemp(prefix="frond-repl-")
                try:
                    self._spawn(sandboxed_argv(argv, self._scratch, shared=True), env, worker_end)
                    return
                except CodeInterpreterError as exc:
                    _confine_failures[key] = str(exc)
            self.unconfined_reason = _confine_failures.get(key, why)
        else:
            self.unconfined_reason = "turned off"
        self._spawn(argv, env, worker_end)

    def _spawn(self, argv: list[str], env: dict[str, str], worker_end: socket.socket) -> None:
        try:
            proc = subprocess.Popen(
                argv,
                cwd=self.cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # only the sandbox helper writes here; the worker sends it to /dev/null
                text=True,
                encoding="utf-8",
                start_new_session=True,
                env=env,
                pass_fds=(worker_end.fileno(),),
            )
        except OSError as exc:
            raise CodeInterpreterError(f"could not start the Python worker: {exc}") from exc
        self._attach(proc)

    def _attach(self, proc: _Process) -> None:
        """Talk to ``proc`` from now on, once it says it is ready."""
        self._proc = proc
        self._inbox = queue.Queue()
        threading.Thread(target=self._pump, args=(proc,), name="frond-repl-reader", daemon=True).start()
        deadline = time.monotonic() + 15
        ready = self._next(0.1)
        while ready is _IDLE and time.monotonic() < deadline:
            ready = self._next(0.1)
        if ready is None or ready.get("type") != "ready":
            stderr, proc.stderr = proc.stderr, None  # read only once the process group is dead: then it ends
            self._kill()
            detail = ""
            if stderr is not None:
                with contextlib.suppress(OSError, ValueError):
                    detail = stderr.read().strip()
                stderr.close()
            raise CodeInterpreterError(f"Python worker failed to start: {detail or repr(ready)}")
        self.confinement = str(ready.get("sandbox") or "")

    def _pump(self, proc: _Process) -> None:
        assert proc.stdout is not None
        inbox = self._inbox
        for line in proc.stdout:
            try:
                inbox.put(json.loads(line))
            except json.JSONDecodeError:
                continue
        inbox.put(None)

    def _send(self, message: dict[str, Any]) -> None:
        proc = self._proc
        if proc is None or proc.stdin is None:
            raise CodeInterpreterError("Python worker is not running")
        data = json.dumps(message, separators=(",", ":"), default=repr)
        with self._send_lock:
            try:
                proc.stdin.write(data + "\n")
                proc.stdin.flush()
            except (BrokenPipeError, OSError) as exc:
                raise CodeInterpreterError(f"lost connection to the Python worker: {exc}") from exc

    def _next(self, timeout: float) -> dict[str, Any] | None:
        """The next message from the worker; ``_IDLE`` if none arrived in time, None at end of stream."""
        try:
            return self._inbox.get(timeout=timeout)
        except queue.Empty:
            return _IDLE

    def interrupt(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            with contextlib.suppress(ProcessLookupError):
                os.kill(self._proc.pid, signal.SIGINT)

    def _kill(self) -> None:
        proc, self._proc = self._proc, None
        if proc is None:
            return
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(proc.pid, signal.SIGKILL)
        with contextlib.suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=2)
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            with contextlib.suppress(OSError):
                if stream is not None:
                    stream.close()
        if isinstance(proc, _Forked):
            proc.channel.close()

    def fork(self) -> ReplSession:
        """A new session whose worker is a copy of this one's, namespace and all (ledger B6).

        The copy inherits the worker's confinement, and from then on the two run independently: what one defines
        or changes, the other never sees. Only an idle worker that this session started can fork. The copy calls
        the same host tools; give it others (``copy.tools.update``) to point it at another directory.
        """
        if not self._exec_lock.acquire(blocking=False):
            raise CodeInterpreterError("the REPL is executing code; fork it between steps")
        try:
            self.start()
            if self._forks is None or self._proc is None:
                raise CodeInterpreterError("this REPL cannot fork: it is itself a copy")
            mine, theirs = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                self._send({"type": "fork"})
                socket.send_fds(self._forks, [b"f"], [theirs.fileno()])
            finally:
                theirs.close()
            deadline = time.monotonic() + 15
            reply = self._next(0.1)
            while reply is _IDLE and time.monotonic() < deadline:
                reply = self._next(0.1)
            if reply is None or reply.get("type") != "forked":
                mine.close()
                raise CodeInterpreterError(f"the Python worker did not fork: {reply!r}")
            copy = ReplSession(
                self.cwd,
                control=self.control,
                on_output=self.on_output,
                timeout=self.timeout,
                policy=self.policy,
                sandbox=self.sandbox,
            )
            copy._tools = dict(self._tools)
            copy.output_fields = self.output_fields
            copy.names = list(self.names)
            copy.unconfined_reason = self.unconfined_reason
            copy._attach(_Forked(int(reply["pid"]), mine))
            return copy
        finally:
            self._exec_lock.release()

    def restart(self) -> None:
        self._kill()
        self.restarts += 1
        self.start()

    def shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._proc is not None and self._proc.poll() is None:
            with contextlib.suppress(Exception):
                self._send({"type": "shutdown"})
            with contextlib.suppress(subprocess.TimeoutExpired):
                self._proc.wait(timeout=1)
        self._kill()
        if self._forks is not None:
            self._forks.close()
        self._pool.shutdown(wait=False, cancel_futures=True)
        if self._scratch is not None:
            shutil.rmtree(self._scratch, ignore_errors=True)

    # ── execution ────────────────────────────────────────────────────────────

    def execute(self, code: str, variables: dict[str, Any] | None = None) -> Any:
        if not self._exec_lock.acquire(blocking=False):
            raise CodeInterpreterError("the REPL is already executing code")
        try:
            return self._execute(code, variables or {})
        finally:
            self._exec_lock.release()

    def _execute(self, code: str, variables: dict[str, Any]) -> Any:
        if self._proc is None or self._proc.poll() is not None:
            if self._proc is not None:
                self._kill()
                self.restarts += 1
            self.start()
        try:
            json.dumps(variables)
        except (TypeError, ValueError) as exc:
            raise CodeInterpreterError(f"REPL variables must be JSON-compatible: {exc}") from exc
        tools = {
            name: {"doc": inspect.getdoc(fn) or "", "signature": _signature_text(fn)}
            for name, fn in self._tools.items()
        }
        context = contextvars.copy_context()
        self._send(
            {
                "type": "execute",
                "code": code,
                "variables": variables,
                "tools": tools,
                "output_fields": self.output_fields,
            }
        )
        started = time.monotonic()
        interrupted_at: float | None = None
        reason = ""
        while True:
            if interrupted_at is None:
                if self.control.cancelled():
                    reason, interrupted_at = "cancelled", time.monotonic()
                    self.interrupt()
                elif time.monotonic() - started > self.timeout:
                    reason, interrupted_at = "timeout", time.monotonic()
                    self.interrupt()
            elif time.monotonic() - interrupted_at > 3.0:
                # The code ignored SIGINT (e.g. stuck in C); the session has to go.
                self._kill()
                self.restarts += 1
                if reason == "cancelled":
                    raise TurnCancelled()
                raise CodeExecutionError(
                    f"Execution exceeded {self.timeout:.0f}s and did not stop on interrupt; the REPL was "
                    "restarted and all variables were lost. Re-create what you need and keep steps shorter."
                )
            message = self._next(0.1)
            if message is _IDLE:
                continue
            if message is None:
                self._kill()
                self.restarts += 1
                raise CodeExecutionError(
                    "The Python worker crashed (possibly out of memory or a fatal error in native code). It "
                    "was restarted; all variables were lost."
                )
            kind = message.get("type")
            if kind == "stdout":
                if self.on_output is not None:
                    self.on_output(message.get("text", ""))
            elif kind == "tool_request":
                self._pool.submit(context.copy().run, self._run_tool, message)
            elif kind == "done":
                return self._finish(message, reason)

    def _run_tool(self, request: dict[str, Any]) -> None:
        name = request.get("name", "")
        fn = self._tools.get(name)
        try:
            if fn is None:
                raise NameError(f"no tool named {name!r}")
            if self.control.cancelled():
                raise TurnCancelled()
            with dspy.context(send_stream=None):
                value = _call_tool(fn, request.get("args") or [], request.get("kwargs") or {})
            try:
                json.dumps(value)
            except (TypeError, ValueError):
                value = json.loads(json.dumps(value, default=repr))
            reply = {"type": "tool_result", "id": request["id"], "value": value}
        except TurnCancelled:
            reply = {
                "type": "tool_error",
                "id": request["id"],
                "error_type": "KeyboardInterrupt",
                "message": "turn cancelled by the user",
            }
        except Exception as exc:
            reply = {
                "type": "tool_error",
                "id": request["id"],
                "error_type": type(exc).__name__,
                "message": _tool_message(name, exc),
            }
        with contextlib.suppress(CodeInterpreterError):
            self._send(reply)

    def _finish(self, message: dict[str, Any], reason: str) -> Any:
        if "names" in message:  # code that did not compile ran nothing, so the namespace is as it was
            self.names = list(message["names"] or [])
        status = message.get("status")
        stdout = message.get("stdout") or ""
        warning = message.get("warning")
        if warning:
            stdout = (stdout + "\n" if stdout else "") + f"[warning] {warning}"
        if status == "final":
            return FinalOutput(message.get("value"))
        if status == "interrupted" or reason:
            if reason == "cancelled" or self.control.cancelled():
                raise TurnCancelled()
            raise CodeExecutionError(
                (stdout + "\n" if stdout else "")
                + f"Execution exceeded the {self.timeout:.0f}s step limit and was interrupted (variables kept). "
                "Use sh(..., background=True) for long-running commands."
            )
        if status == "syntax":
            raise SyntaxError(message.get("error", "invalid syntax"))
        if status == "error":
            error = message.get("error", "error")
            raise CodeExecutionError((stdout.rstrip() + "\n" if stdout.strip() else "") + error)
        return stdout


def _tool_message(name: str, exc: Exception) -> str:
    text = str(exc) or type(exc).__name__
    # dspy.Tool reports argument validation problems as "Arg x is invalid"; say which tool it was.
    if isinstance(exc, (TypeError, ValueError)) and not text.startswith(name):
        return f"{name}(): {text}"
    return text


class ReplLease:
    """The persistent session as handed to one ``RLM.forward``; shutting the lease down only returns it."""

    def __init__(self, session: ReplSession, release: Callable[[], None]) -> None:
        self._session = session
        self._release = release
        self._released = False

    @property
    def tools(self) -> dict[str, Callable[..., Any]]:
        return self._session.tools

    @property
    def output_fields(self) -> list[dict[str, Any]] | None:
        return self._session.output_fields

    @output_fields.setter
    def output_fields(self, value: list[dict[str, Any]] | None) -> None:
        self._session.output_fields = value

    def start(self) -> None:
        self._session.start()

    def execute(self, code: str, variables: dict[str, Any] | None = None) -> Any:
        return self._session.execute(code, variables)

    @property
    def names(self) -> list[str]:
        return self._session.names

    def shutdown(self) -> None:
        if not self._released:
            self._released = True
            self._release()


class ReplPool:
    """The interpreter factory given to dspy.RLM.

    The first interpreter requested while the root session is idle is a lease on that session, so the
    namespace persists across turns. Requests made while it is busy (sub-agents built inside the REPL via
    the dspy facade, or frond's own sub-agents) get a fresh worker that is discarded afterwards.
    """

    execution_instructions = EXECUTION_INSTRUCTIONS

    def __init__(
        self,
        cwd: Path,
        control: TurnControl,
        *,
        on_output: OutputSink | None = None,
        timeout: float = 900.0,
        policy: str = "strict",
        sandbox: bool = True,
    ) -> None:
        self.cwd = cwd
        self.control = control
        self.timeout = timeout
        self.policy = policy
        self.sandbox = sandbox
        self.root = ReplSession(
            cwd, control=control, on_output=on_output, timeout=timeout, policy=policy, sandbox=sandbox
        )
        self._busy = False
        self._lock = threading.Lock()

    def __call__(self) -> ReplLease | ReplSession:
        with self._lock:
            if not self._busy:
                self._busy = True
                return ReplLease(self.root, self._release)
        return self.ephemeral()

    def ephemeral(self) -> ReplSession:
        return ReplSession(
            self.cwd, control=self.control, timeout=self.timeout, policy=self.policy, sandbox=self.sandbox
        )

    def _release(self) -> None:
        with self._lock:
            self._busy = False

    def reset(self) -> None:
        """Forget all REPL state (the /reset command)."""
        self.root.restart()

    def close(self) -> None:
        self.root.shutdown()
