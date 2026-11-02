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
import threading
import time
from collections.abc import Callable
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

_ids = itertools.count(1)


def next_command_id() -> int:
    return next(_ids)


def clean_output(text: str) -> str:
    """Strip ANSI escapes and resolve carriage-return overwrites the way a terminal would show them."""
    text = ANSI_RE.sub("", text).replace("\r\n", "\n")
    if "\r" not in text:
        return text
    return "\n".join(line.rsplit("\r", 1)[-1] if "\r" in line else line for line in text.split("\n"))


def shell_argv(command: str) -> list[str]:
    bash = shutil.which("bash")
    return [bash, "-c", command] if bash else ["/bin/sh", "-c", command]


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

    def run(self, command: str, *, cwd: Path, timeout: float, scope: str = "") -> CommandResult:
        cmd_id = next_command_id()
        log_path = self.log_dir / f"cmd-{cmd_id}.log"
        self.emit(CommandStarted(cmd_id, command, str(cwd), background=False, scope=scope))
        start = time.monotonic()
        try:
            proc = subprocess.Popen(
                shell_argv(command),
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                env=self.env(),
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
                    ready, _, _ = select.select([fd], [], [], 0.05)
                    if ready:
                        data = os.read(fd, 65536)
                        if not data:
                            break
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
            with self._lock:
                self._active.discard(proc)
            if proc.poll() is None and status == "ok":
                with contextlib.suppress(subprocess.TimeoutExpired):
                    proc.wait(timeout=5)
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
