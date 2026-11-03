"""Running shell commands for the agent: foreground commands with live output, and background jobs.

Every command runs in its own session (process group) so that cancelling a turn, a timeout, or quitting
frond can take down the whole tree a command spawned, not just the shell.
"""

from __future__ import annotations

import codecs
import contextlib
import itertools
import os
import re
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from frond.events import (
    CommandFinished,
    CommandOutput,
    CommandStarted,
    CommandStatus,
    Emit,
    JobInfo,
    JobsChanged,
)

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[@-Z\\-_]")
COMMAND_ENV = {
    "PAGER": "cat",
    "GIT_PAGER": "cat",
    "MANPAGER": "cat",
    "GIT_TERMINAL_PROMPT": "0",
    "NO_COLOR": "1",
    "CLICOLOR": "0",
    "FORCE_COLOR": "0",
    "TERM": "dumb",
    "PYTHONUNBUFFERED": "1",
    "FROND_AGENT": "1",
}
MAX_MEMORY_CHARS = 4_000_000
# Variables a confined process (the REPL worker, a read-only agent's command) never needs, and which an injected
# instruction would want: credentials by name, and URLs that embed a password (user:secret@host).
CREDENTIAL_NAME = re.compile(r"KEY|TOKEN|SECRET|PASSW|CREDENTIAL|AUTH|COOKIE|SESSION", re.IGNORECASE)
CREDENTIAL_IN_URL = re.compile(r"://[^/\s:@]+:[^/\s@]+@")

_ids = itertools.count(1)


def next_command_id() -> int:
    return next(_ids)


def scrubbed_env(env: Mapping[str, str]) -> dict[str, str]:
    """``env`` without the variables that look like credentials.

    Not a security boundary on its own: a process running as the same user can still read its parent's
    /proc/PID/environ and the user's files. It matters together with the sandbox, which cuts the network.
    """
    return {k: v for k, v in env.items() if not CREDENTIAL_NAME.search(k) and not CREDENTIAL_IN_URL.search(v)}


def clean_output(text: str) -> str:
    """Strip ANSI escapes and resolve carriage-return overwrites the way a terminal would show them."""
    text = ANSI_RE.sub("", text).replace("\r\n", "\n")
    if "\r" not in text:
        return text
    return "\n".join(line.rsplit("\r", 1)[-1] if "\r" in line else line for line in text.split("\n"))


def shell_argv(command: str) -> list[str]:
    bash = shutil.which("bash")
    return [bash, "-c", command] if bash else ["/bin/sh", "-c", command]


SANDBOX_HELPER = Path(__file__).with_name("_sandbox.py")
SANDBOX_UNAVAILABLE = 125
_sandbox_probes: dict[str, tuple[bool, str]] = {}
_sandbox_lock = threading.Lock()


def sandboxed_argv(argv: list[str], tmpdir: str, *, shared: bool = False) -> list[str]:
    """``argv`` run under frond's read-only sandbox (see _sandbox.py): it cannot change the filesystem.

    With ``shared``, ``tmpdir`` stays writable and visible outside the sandbox instead of becoming private.
    """
    flag = ["--shared-tmpdir"] if shared else []
    return [sys.executable, "-I", str(SANDBOX_HELPER), *flag, tmpdir, "--", *argv]


def sandbox_status(cwd: Path) -> tuple[bool, str]:
    """(available, the sandbox's name or why there is none), probed once per process."""
    key = os.environ.get("FROND_SANDBOX", "")
    with _sandbox_lock:
        if key not in _sandbox_probes:
            tmp = tempfile.mkdtemp(prefix="frond-sandbox-probe-")
            try:
                probe = subprocess.run(
                    sandboxed_argv(["/bin/sh", "-c", 'printf %s "$FROND_SANDBOXED"'], tmp),
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    stdin=subprocess.DEVNULL,
                )
                ok = probe.returncode == 0 and bool(probe.stdout.strip())
                why = probe.stdout.strip() if ok else (probe.stderr.strip() or f"exit {probe.returncode}")
                _sandbox_probes[key] = (ok, why.removeprefix("frond-sandbox: "))
            except (OSError, subprocess.TimeoutExpired) as exc:
                _sandbox_probes[key] = (False, str(exc))
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
        return _sandbox_probes[key]


def kill_group(proc: subprocess.Popen[bytes], grace: float = 1.5) -> None:
    """SIGTERM the command's process group, then SIGKILL whatever is left after ``grace`` seconds."""
    if proc.poll() is not None:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(proc.pid, signal.SIGKILL)  # reap stragglers that outlived the shell
        return
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        pass
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(proc.pid, signal.SIGKILL)
    with contextlib.suppress(subprocess.TimeoutExpired):
        proc.wait(timeout=grace)


@dataclass(frozen=True, slots=True)
class CommandResult:
    command: str
    exit_code: int | None
    output: str
    duration: float
    status: CommandStatus
    log_path: str
    total_chars: int

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def truncate_middle(text: str, limit: int, *, note: str = "") -> str:
    """Keep the head and (mostly) the tail: errors and summaries tend to live at the end of output."""
    if len(text) <= limit:
        return text
    head = limit // 5
    tail = limit - head
    omitted = len(text) - limit
    return f"{text[:head]}\n\n… [{omitted:,} characters omitted{note}] …\n\n{text[-tail:]}"


class ShellRunner:
    """Runs foreground commands, streaming output as events and honouring cancellation."""

    def __init__(self, root: Path, log_dir: Path, emit: Emit, cancelled: Callable[[], bool]) -> None:
        self.root = root
        self.log_dir = log_dir
        self.emit = emit
        self.cancelled = cancelled
        self._active: set[subprocess.Popen[bytes]] = set()
        self._lock = threading.Lock()

    def env(self) -> dict[str, str]:
        return {**os.environ, **COMMAND_ENV}

    def kill_all(self) -> None:
        with self._lock:
            procs = list(self._active)
        for proc in procs:
            kill_group(proc, grace=0.5)

    def run(
        self, command: str, *, cwd: Path, timeout: float, scope: str = "", sandboxed: bool = False
    ) -> CommandResult:
        cmd_id = next_command_id()
        log_path = self.log_dir / f"cmd-{cmd_id}.log"
        self.emit(CommandStarted(cmd_id, command, str(cwd), background=False, scope=scope))
        start = time.monotonic()
        argv = shell_argv(command)
        env = self.env()
        scratch = None
        if sandboxed:
            scratch = tempfile.mkdtemp(prefix="sandbox-", dir=self.log_dir)
            argv = sandboxed_argv(argv, scratch)
            env = scrubbed_env(env)
        try:
            return self._run(command, argv, cmd_id, log_path, cwd, timeout, start, env)
        finally:
            if scratch is not None:
                shutil.rmtree(scratch, ignore_errors=True)

    def _run(
        self,
        command: str,
        argv: list[str],
        cmd_id: int,
        log_path: Path,
        cwd: Path,
        timeout: float,
        start: float,
        env: dict[str, str],
    ) -> CommandResult:
        try:
            proc = subprocess.Popen(
                argv,
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                env=env,
            )
        except OSError as exc:
            self.emit(CommandOutput(cmd_id, f"failed to start: {exc}\n"))
            self.emit(CommandFinished(cmd_id, None, 0.0, "failed"))
            return CommandResult(command, None, f"failed to start: {exc}", 0.0, "failed", str(log_path), 0)
        with self._lock:
            self._active.add(proc)
        status: CommandStatus = "ok"
        chunks: list[str] = []
        size = 0
        pending = ""
        last_emit = 0.0
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        assert proc.stdout is not None
        fd = proc.stdout.fileno()
        exited_at: float | None = None
        output_closed = False
        try:
            with open(log_path, "w", encoding="utf-8") as log:
                while True:
                    if self.cancelled():
                        status = "cancelled"
                        kill_group(proc)
                        break
                    now = time.monotonic()
                    if now - start > timeout:
                        status = "timeout"
                        kill_group(proc)
                        break
                    if output_closed:
                        # EOF means nothing holds the pipe any more, not that the command has exited (it may
                        # have closed or redirected its output); keep waiting, with cancel and timeout in force.
                        if proc.poll() is not None:
                            break
                        time.sleep(0.05)
                        continue
                    ready, _, _ = select.select([fd], [], [], 0.05)
                    if ready:
                        data = os.read(fd, 65536)
                        if not data:
                            output_closed = True
                            continue
                        text = decoder.decode(data)
                        log.write(text)
                        if size < MAX_MEMORY_CHARS:
                            chunks.append(text)
                            size += len(text)
                        pending += text
                    if proc.poll() is not None:
                        # The shell exited; stop once the pipe goes quiet. A background grandchild may keep
                        # the pipe open forever, so we do not wait for EOF beyond a short drain window.
                        exited_at = exited_at or time.monotonic()
                        if not ready and time.monotonic() - exited_at > 0.15:
                            break
                    if pending and (time.monotonic() - last_emit > 0.05 or len(pending) > 8192):
                        self.emit(CommandOutput(cmd_id, clean_output(pending)))
                        pending, last_emit = "", time.monotonic()
                tail = decoder.decode(b"", final=True)
                if tail:
                    log.write(tail)
                    chunks.append(tail)
                    pending += tail
        finally:
            if proc.poll() is None:  # only after an unexpected error: every normal exit has reaped or killed it
                kill_group(proc)
            with self._lock:
                self._active.discard(proc)
            with contextlib.suppress(OSError):
                proc.stdout.close()
        if pending:
            self.emit(CommandOutput(cmd_id, clean_output(pending)))
        exit_code = proc.poll()
        if status == "ok" and exit_code not in (0, None):
            status = "failed"
        duration = time.monotonic() - start
        self.emit(CommandFinished(cmd_id, exit_code, duration, status))
        output = clean_output("".join(chunks))
        return CommandResult(command, exit_code, output, duration, status, str(log_path), len(output))


@dataclass
class Job:
    job_id: int
    command: str
    proc: subprocess.Popen[bytes]
    started: float
    log_path: Path
    cwd: Path

    def info(self) -> JobInfo:
        code = self.proc.poll()
        return JobInfo(self.job_id, self.command, self.proc.pid, code is None, code, self.started, str(self.log_path))


class JobManager:
    """Long-running background processes (dev servers, watchers) that outlive a single tool call."""

    def __init__(self, log_dir: Path, emit: Emit) -> None:
        self.log_dir = log_dir
        self.emit = emit
        self._jobs: dict[int, Job] = {}
        self._ids = itertools.count(1)
        self._lock = threading.Lock()

    def set_emit(self, emit: Emit) -> None:
        self.emit = emit

    def _changed(self) -> None:
        self.emit(JobsChanged(tuple(job.info() for job in self.snapshot())))

    def snapshot(self) -> list[Job]:
        with self._lock:
            return list(self._jobs.values())

    def get(self, job_id: int) -> Job:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            known = ", ".join(str(j) for j in self._jobs) or "none"
            raise KeyError(f"no background job {job_id} (known jobs: {known})")
        return job

    def start(self, command: str, cwd: Path, env: dict[str, str], scope: str = "") -> Job:
        job_id = next(self._ids)
        log_path = self.log_dir / f"job-{job_id}.log"
        cmd_id = next_command_id()
        self.emit(CommandStarted(cmd_id, command, str(cwd), background=True, scope=scope))
        log = open(log_path, "wb")  # noqa: SIM115 - handed to the child; closed by the watcher
        try:
            proc = subprocess.Popen(
                shell_argv(command),
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                env=env,
            )
        except OSError:
            log.close()
            self.emit(CommandFinished(cmd_id, None, 0.0, "failed"))
            raise
        job = Job(job_id, command, proc, time.time(), log_path, cwd)
        with self._lock:
            self._jobs[job_id] = job
        self.emit(CommandFinished(cmd_id, None, 0.0, "background"))
        self._changed()

        def watch() -> None:
            proc.wait()
            log.close()
            self._changed()

        threading.Thread(target=watch, name=f"frond-job-{job_id}", daemon=True).start()
        return job

    def output(self, job_id: int, tail: int = 100) -> str:
        job = self.get(job_id)
        try:
            data = job.log_path.read_bytes()
        except OSError:
            return ""
        text = clean_output(data[-2_000_000:].decode("utf-8", errors="replace"))
        lines = text.splitlines()
        return "\n".join(lines[-tail:]) if tail > 0 else text

    def kill(self, job_id: int) -> int | None:
        job = self.get(job_id)
        kill_group(job.proc)
        self._changed()
        return job.proc.poll()

    def kill_all(self) -> None:
        for job in self.snapshot():
            kill_group(job.proc, grace=0.5)
