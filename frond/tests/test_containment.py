"""The REPL worker holds no credentials and has no network, and where the OS allows, a sandbox enforces both."""

from __future__ import annotations

import ctypes
import errno
import os
import shutil
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from dspy.primitives.code_interpreter import CodeExecutionError

from frond.agent.control import TurnControl
from frond.agent.repl import ReplSession
from frond.agent.scripted import Step
from frond.agent.shell import sandbox_status, scrubbed_env
from frond.events import Notice
from tests.helpers import WorkspaceCase, scripted_agent

SECRETS = {
    "ANTHROPIC_API_KEY": "sk-ant-test",
    "GITHUB_TOKEN": "ghp_test",
    "DATABASE_URL": "postgres://app:hunter2@db.internal/app",
}


class ScrubbedEnvTest(unittest.TestCase):
    def test_credentials_go_and_everything_else_stays(self):
        env = {
            **SECRETS,
            "AWS_SECRET_ACCESS_KEY": "x",
            "SSH_AUTH_SOCK": "/tmp/ssh-agent.sock",
            "PATH": "/usr/bin",
            "HOME": "/home/u",
            "LANG": "C.UTF-8",
            "CACHE_URL": "redis://cache.internal:6379/0",
        }
        kept = {"PATH": "/usr/bin", "HOME": "/home/u", "LANG": "C.UTF-8", "CACHE_URL": "redis://cache.internal:6379/0"}
        self.assertEqual(scrubbed_env(env), kept)


class Listener:
    """A TCP server on the host that records whether anything reached it."""

    def __init__(self) -> None:
        self.sock = socket.create_server(("127.0.0.1", 0))
        self.sock.settimeout(1.0)
        self.port = self.sock.getsockname()[1]

    def reached(self) -> bool:
        try:
            conn, _ = self.sock.accept()
        except TimeoutError:
            return False
        conn.close()
        return True

    def close(self) -> None:
        self.sock.close()


class WorkerCase(unittest.TestCase):
    sandbox = ""  # FROND_SANDBOX for this case: "" picks the strongest available

    def start(self) -> ReplSession:
        patcher = mock.patch.dict(os.environ, {**SECRETS, "FROND_SANDBOX": self.sandbox})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.workspace = Path(tempfile.mkdtemp(prefix="frond-ws-"))
        self.addCleanup(shutil.rmtree, self.workspace, True)
        session = ReplSession(self.workspace, control=TurnControl(), timeout=10)
        self.addCleanup(session.shutdown)
        session.start()
        return session

    def listener(self) -> Listener:
        listener = Listener()
        self.addCleanup(listener.close)
        return listener


class WorkerTest(WorkerCase):
    def test_no_credentials_and_no_network_from_python(self):
        session = self.start()
        names = "('ANTHROPIC_API_KEY', 'GITHUB_TOKEN', 'DATABASE_URL')"
        self.assertEqual(session.execute(f"import os\nprint([k for k in {names} if k in os.environ])"), "[]\n")
        listener = self.listener()
        for code in (
            f"import socket\nsocket.create_connection(('127.0.0.1', {listener.port}), timeout=1)",
            f"import socket\nsocket.socket().connect(('127.0.0.1', {listener.port}))",
            f"import urllib.request\nurllib.request.urlopen('http://127.0.0.1:{listener.port}/', timeout=1)",
            "import socket\nsocket.getaddrinfo('example.com', 443)",
            "import socket\nsocket.socket(socket.AF_UNIX).connect('/var/run/docker.sock')",
        ):
            with self.subTest(code=code.splitlines()[-1]), self.assertRaisesRegex(CodeExecutionError, "no network"):
                session.execute(code)
        self.assertFalse(listener.reached())
        # threads can still talk to each other: asyncio's wake-up pipe is a socketpair
        self.assertEqual(session.execute("import asyncio\nprint(asyncio.run(asyncio.sleep(0, 'ok')))"), "ok\n")

    def test_scratch_files_can_be_read_from_outside(self):
        session = self.start()
        code = (
            "import os, tempfile\np = os.path.join(tempfile.gettempdir(), 'note.txt')\n"
            "open(p, 'w').write('hi')\nprint(p)"
        )
        path = Path(session.execute(code).strip())
        self.assertEqual(path.read_text(), "hi")  # where commands run by sh() can read it too


def landlock_abi() -> int:
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    return int(libc.syscall(444, None, ctypes.c_size_t(0), ctypes.c_uint32(1)))


@unittest.skipUnless(sys.platform.startswith("linux"), "the Linux sandboxes")
class ConfinedWorkerTest(WorkerCase):
    """ctypes calls the C library directly, past the audit hook: only the OS can stop what follows."""

    def confined(self, choice: str) -> ReplSession:
        self.sandbox = choice
        with mock.patch.dict(os.environ, {"FROND_SANDBOX": choice}):
            available, why = sandbox_status(Path.cwd())
        if not available:
            self.skipTest(f"{choice}: {why}")
        session = self.start()
        self.assertEqual(session.confinement, choice)
        return session

    def assert_no_write(self, session: ReplSession) -> None:
        target = self.workspace / "escaped.txt"
        code = (
            "import ctypes, os\nlibc = ctypes.CDLL(None, use_errno=True)\n"
            f"fd = libc.open({os.fsencode(target)!r}, os.O_WRONLY | os.O_CREAT, 0o644)\n"
            "print(fd, ctypes.get_errno())"
        )
        fd, error = map(int, session.execute(code).split())
        self.assertEqual(fd, -1)
        self.assertIn(error, (errno.EROFS, errno.EACCES))
        self.assertFalse(target.exists())

    def assert_no_connection(self, session: ReplSession) -> None:
        listener = self.listener()
        code = (
            "import ctypes, socket, struct\nlibc = ctypes.CDLL(None, use_errno=True)\n"
            "fd = libc.socket(socket.AF_INET, socket.SOCK_STREAM, 0)\n"
            f"addr = struct.pack('=H', socket.AF_INET) + struct.pack('!H', {listener.port})"
            " + socket.inet_aton('127.0.0.1') + bytes(8)\n"
            "print(libc.connect(fd, addr, len(addr)))"
        )
        self.assertEqual(session.execute(code).strip(), "-1")
        self.assertFalse(listener.reached())

    def test_namespaces(self):
        session = self.confined("namespaces")
        self.assert_no_write(session)
        self.assert_no_connection(session)

    def test_landlock(self):
        session = self.confined("landlock")
        self.assert_no_write(session)
        if landlock_abi() < 4:
            self.skipTest("Landlock restricts TCP only from ABI 4")
        self.assert_no_connection(session)


class UnconfinedWorkerTest(WorkerCase):
    sandbox = "none"

    def test_it_still_runs_without_credentials_or_network(self):
        session = self.start()
        self.assertEqual(session.confinement, "")
        self.assertIn("FROND_SANDBOX=none", session.unconfined_reason)
        self.assertEqual(session.execute("import os\nprint('ANTHROPIC_API_KEY' in os.environ)"), "False\n")
        with self.assertRaisesRegex(CodeExecutionError, "no network"):
            session.execute("import socket\nsocket.socket()")


class ConfinementNoticeTest(WorkspaceCase):
    def test_the_user_hears_once_when_the_repl_runs_unconfined(self):
        with mock.patch.dict(os.environ, {"FROND_SANDBOX": "none"}):
            steps = [Step("a", "print(1)"), Step("b", "print(2)"), Step("c", "SUBMIT(response='done')")]
            agent, _ = scripted_agent(self, steps)
            agent.run_turn("go")
        notices = [n for n in self.of_type(Notice) if "without an OS sandbox" in n.text]
        self.assertEqual(len(notices), 1)
        self.assertIn("FROND_SANDBOX=none", notices[0].text)


class ReadOnlyCommandTest(WorkspaceCase):
    def test_read_only_agents_commands_get_no_credentials(self):
        available, why = sandbox_status(self.root)
        if not available:
            self.skipTest(why)
        with mock.patch.dict(os.environ, SECRETS):
            result = self.toolbox(read_only=True).sh("echo key=${ANTHROPIC_API_KEY:-none} db=${DATABASE_URL:-none}")
        self.assertIn("key=none db=none", result["output"])


if __name__ == "__main__":
    unittest.main()
