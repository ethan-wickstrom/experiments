"""The forkable REPL (B6): a copy of an idle worker keeps its namespace, then runs on its own, confined like it."""

from __future__ import annotations

import os
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from dspy.primitives.code_interpreter import CodeExecutionError

from frond.agent.repl import ReplSession
from frond.agent.shell import sandbox_status
from tests import test_containment


class ForkTest(test_containment.WorkerCase):
    def fork(self, session: ReplSession) -> ReplSession:
        copy = session.fork()
        self.addCleanup(copy.shutdown)
        return copy

    def test_a_copy_keeps_the_namespace_then_runs_on_its_own(self):
        session = self.start()
        session.execute("x = 41\nimport math")
        copy = self.fork(session)
        self.assertNotEqual(copy.pid, session.pid)
        self.assertEqual(copy.execute("x += 1\nprint(x, math.pi > 3)"), "42 True\n")
        self.assertEqual(session.execute("print(x)"), "41\n")
        session.execute("only_in_the_original = 1")
        self.assertEqual(copy.execute("print('only_in_the_original' in globals())"), "False\n")
        self.assertIn("x", " ".join(copy.names))

    def test_tools_called_from_a_copy_reach_the_host(self):
        session = self.start()
        session.tools["shout"] = lambda text: text.upper()
        session.execute("pass")  # the worker learns the tools
        copy = self.fork(session)
        copy.tools["shout"] = lambda text: text.upper() + "!"  # a copy can be given tools of its own
        self.assertEqual(copy.execute("print(shout('hi'))"), "HI!\n")
        self.assertEqual(session.execute("print(shout('hi'))"), "HI\n")

    def test_each_copy_has_scratch_space_of_its_own(self):
        session = self.start()
        copy = self.fork(session)
        code = "import tempfile\nprint(tempfile.gettempdir())"
        self.assertNotEqual(copy.execute(code), session.execute(code))

    def test_ending_or_interrupting_a_copy_leaves_the_original(self):
        session = self.start()
        session.execute("x = 1")
        copy = self.fork(session)
        outcome: list[str] = []

        def spin() -> None:
            try:
                copy.execute("while True:\n    pass")
            except CodeExecutionError as exc:
                outcome.append(str(exc))

        runner = threading.Thread(target=spin)
        runner.start()
        time.sleep(0.5)
        copy.interrupt()
        runner.join(10)
        self.assertTrue(outcome and "interrupted" in outcome[0], outcome)
        pid = copy.pid
        copy.shutdown()
        assert pid is not None
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and _alive(pid):
            time.sleep(0.05)
        self.assertFalse(_alive(pid))  # reaped by the original worker, not left a zombie
        self.assertEqual(session.execute("print(x)"), "1\n")

    def test_the_original_takes_its_running_copies_down_with_it(self):  # Devin, #14 (F22)
        session = self.start()
        copy = self.fork(session)
        pid = copy.pid
        runner = threading.Thread(target=lambda: _quietly(copy.execute, "while True:\n    pass"), daemon=True)
        runner.start()
        time.sleep(0.3)
        session.shutdown()
        assert pid is not None
        self.assertTrue(_gone(pid), "a copy outlived its original's shutdown")

    def test_a_copy_dies_with_its_original_worker_even_if_the_host_does_not_ask(self):  # F22: the host crashed
        if not sys.platform.startswith("linux"):
            self.skipTest("PR_SET_PDEATHSIG is Linux's")
        session = self.start()
        copy = self.fork(session)
        pid, original = copy.pid, session.pid
        assert pid is not None and original is not None
        os.kill(original, 9)
        self.assertTrue(_gone(pid), "a copy outlived its original worker")

    def test_a_copys_scratch_space_goes_when_it_does(self):  # Devin, #14 (F23)
        session = self.start()
        copy = self.fork(session)
        scratch = Path(copy.execute("import tempfile\nprint(tempfile.gettempdir())").strip())
        copy.execute(f"open({str(scratch / 'big.bin')!r}, 'wb').write(b'x' * 1000)")
        self.assertTrue(scratch.is_dir())
        copy.shutdown()
        self.assertFalse(scratch.exists())
        self.assertEqual(session.execute("print(1)"), "1\n")

    def test_no_fork_while_the_agents_threads_run(self):  # Devin, #14 (F24): a lock they hold would stay held
        session = self.start()
        session.execute(
            "import threading, time\n"
            "t = threading.Thread(target=time.sleep, args=(30,), name='poller', daemon=True)\n"
            "t.start()"
        )
        with self.assertRaisesRegex(Exception, "threads your code started are still running \\(poller\\)"):
            session.fork()
        self.assertEqual(session.execute("print(t.is_alive())"), "True\n")  # the original is untouched

    def test_a_copy_cannot_fork_again(self):
        session = self.start()
        copy = self.fork(session)
        with self.assertRaisesRegex(Exception, "cannot fork"):
            copy.fork()


def _quietly(fn, *args) -> None:
    try:
        fn(*args)
    except Exception:
        pass


def _gone(pid: int, wait: float = 5.0) -> bool:
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline and _alive(pid):
        time.sleep(0.05)
    return not _alive(pid)


@unittest.skipUnless(sys.platform.startswith("linux"), "the Linux sandboxes")
class ConfinedForkTest(test_containment.ConfinedWorkerTest):
    """A copy is as confined as its original: the same checks, run in the copy."""

    def check(self, choice: str) -> None:
        with mock.patch.dict(os.environ, {"FROND_SANDBOX": choice}):
            available, why = sandbox_status(Path.cwd())
        if not available:
            self.skipTest(f"{choice}: {why}")
        session = self.confined(choice)
        copy = session.fork()
        self.addCleanup(copy.shutdown)
        self.assertEqual(copy.confinement, choice)
        self.assert_no_write(copy)
        self.assert_no_connection(copy)

    def test_namespaces(self):
        self.check("namespaces")

    def test_landlock(self):
        self.check("landlock")


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


if __name__ == "__main__":
    unittest.main()
