"""Read-only agents' commands run in an OS sandbox that refuses every filesystem write (not a command filter)."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from typing import ClassVar
from unittest import mock

from frond.agent.shell import sandbox_status
from tests.helpers import WorkspaceCase

LINUX = sys.platform.startswith("linux")


class SandboxCase(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {"notes.txt": "keep me\n", "pkg/mod.py": "x = 1\n"}
    mode = ""

    def setUp(self) -> None:
        super().setUp()
        patcher = mock.patch.dict(os.environ, {"FROND_SANDBOX": self.mode} if self.mode else {})
        patcher.start()
        self.addCleanup(patcher.stop)
        available, why = sandbox_status(self.root)
        if not available:
            self.skipTest(f"no {self.mode or 'read-only'} sandbox here: {why}")

    def assert_unchanged(self) -> None:
        self.assertEqual((self.root / "notes.txt").read_text(), "keep me\n")
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["notes.txt", "pkg"])

    def check_writes_fail_and_reads_work(self, tools) -> None:
        for command in (
            "echo hi > new.txt",
            "echo more >> notes.txt",
            "sed -i 's/keep/lose/' notes.txt",
            "python3 -c \"open('notes.txt', 'w').write('gone')\"",
            "rm -f notes.txt",
            "mv notes.txt moved.txt",
            "mkdir build",
            "git init -q",
        ):
            result = tools.sh(command)
            self.assertFalse(result["ok"], command)
        self.assert_unchanged()
        self.assertEqual(tools.sh("cat notes.txt")["output"].strip(), "keep me")
        self.assertIn("ok", tools.sh('echo ok > "$TMPDIR/scratch" && cat "$TMPDIR/scratch"')["output"])
        self.assertIn("x = 1", tools.sh("python3 -c \"print(open('pkg/mod.py').read())\"")["output"])


@unittest.skipUnless(LINUX, "Linux namespaces")
class NamespaceSandboxTest(SandboxCase):
    mode = "namespaces"

    def test_every_write_fails_even_metadata(self):
        tools = self.toolbox(read_only=True)
        self.check_writes_fail_and_reads_work(tools)
        self.assertIn("Read-only file system", tools.sh("chmod 600 notes.txt")["output"])
        self.assertEqual(oct((self.root / "notes.txt").stat().st_mode & 0o777), "0o644")
        self.assertEqual(tools.sh("echo $FROND_SANDBOXED")["output"].strip(), "namespaces")

    def test_no_network_but_loopback_works(self):
        tools = self.toolbox(read_only=True)
        code = "import socket; s = socket.socket(); s.bind(('127.0.0.1', 0)); s.listen(); print('loopback ok')"
        self.assertIn("loopback ok", tools.sh(f'python3 -c "{code}"')["output"])
        reach = "import socket; socket.create_connection(('1.1.1.1', 443), timeout=2)"
        self.assertFalse(tools.sh(f'python3 -c "{reach}"')["ok"])


@unittest.skipUnless(LINUX, "Linux Landlock")
class LandlockSandboxTest(SandboxCase):
    mode = "landlock"

    def test_file_writes_fail(self):
        tools = self.toolbox(read_only=True)
        self.check_writes_fail_and_reads_work(tools)
        self.assertEqual(tools.sh("echo $FROND_SANDBOXED")["output"].strip(), "landlock")


class SandboxRefusalTest(WorkspaceCase):
    def test_without_a_sandbox_read_only_commands_do_not_run(self):
        with mock.patch.dict(os.environ, {"FROND_SANDBOX": "none"}):
            tools = self.toolbox(read_only=True)
            with self.assertRaisesRegex(PermissionError, "none is available here"):
                tools.sh("echo hi > created.txt")
        self.assertFalse((self.root / "created.txt").exists())

    def test_read_only_agents_cannot_start_background_jobs(self):
        with self.assertRaisesRegex(PermissionError, "background"):
            self.toolbox(read_only=True).sh("sleep 5", background=True)

    def test_read_only_mode_runs_commands_in_the_sandbox(self):
        if not sandbox_status(self.root)[0]:
            self.skipTest("no sandbox here")
        tools = self.toolbox(mode="readonly")
        result = tools.sh("echo hi > created.txt; echo ran")
        self.assertIn("ran", result["output"])
        self.assertFalse((self.root / "created.txt").exists())

    def test_the_helper_refuses_to_run_anything_without_a_sandbox(self):
        from frond.agent.shell import SANDBOX_HELPER

        env = {**os.environ, "FROND_SANDBOX": "none"}
        proc = subprocess.run(
            [sys.executable, "-I", str(SANDBOX_HELPER), str(self.root), "--", "touch", "made.txt"],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 125)
        self.assertIn("frond-sandbox:", proc.stderr)
        self.assertFalse((self.root / "made.txt").exists())


if __name__ == "__main__":
    unittest.main()
