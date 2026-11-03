"""An incompatible DSPy fails at startup with what changed (R9, B11)."""

from __future__ import annotations

import contextlib
import io
import unittest
from unittest import mock

from dspy.predict import rlm as dspy_rlm

from frond import cli
from frond.agent import compat
from tests.helpers import WorkspaceCase, scripted_agent


class CompatTest(unittest.TestCase):
    def test_the_installed_dspy_matches(self):
        self.assertEqual(compat.problems(), [])

    def test_a_changed_signature_is_named_and_stops_the_cli(self):
        def changed(self, repl, history, iteration):  # parameters frond does not expect
            return None

        err = io.StringIO()
        with mock.patch.object(dspy_rlm.RLM, "_execute_code", changed), contextlib.redirect_stderr(err):
            found = compat.problems()
            code = cli.main(["-p", "hello"])
        self.assertEqual(len(found), 1)
        self.assertIn("RLM._execute_code", found[0])
        self.assertEqual(code, 2)
        self.assertIn("frond needs the DSPy release it was built against", err.getvalue())

    def test_a_missing_internal_is_named(self):
        with (
            mock.patch.object(dspy_rlm, "_strip_code_fences", None),
            mock.patch.object(compat, "EXPECTED", (("dspy.predict.rlm", "gone_entirely", None),)),
        ):
            self.assertEqual(compat.problems(), ["dspy.predict.rlm.gone_entirely is missing"])

    def test_a_helper_that_is_no_longer_callable_is_named(self):  # F41
        with mock.patch.object(dspy_rlm, "_strip_code_fences", "not a function"):
            self.assertEqual(compat.problems(), ["dspy.predict.rlm._strip_code_fences is not callable"])

    def test_a_parameter_that_changed_kind_is_named(self):  # F42: same names, but frond's positional call breaks
        def keyword_only(self, repl, *, code, input_args):
            return None

        with mock.patch.object(dspy_rlm.RLM, "_execute_code", keyword_only):
            found = compat.problems()
        self.assertEqual(len(found), 1)
        self.assertIn("RLM._execute_code", found[0])

    def test_a_signature_that_cannot_be_read_fails_closed(self):  # Devin, #28 (F53)
        with mock.patch("inspect.signature", side_effect=ValueError("no signature")):
            found = compat.problems()
        self.assertTrue(found)
        self.assertTrue(all("cannot be read" in f for f in found), found)

    def test_the_pattern_reply_recovery_matches_with_is_checked(self):  # D46
        from dspy.adapters import chat_adapter

        with mock.patch.object(chat_adapter, "field_header_pattern", "[[ ## (\\w+) ## ]]"):
            self.assertEqual(
                compat.problems(), ["dspy.adapters.chat_adapter.field_header_pattern is not a compiled pattern"]
            )


class LibraryUseTest(WorkspaceCase):
    def test_library_use_is_checked_too(self):  # F44: an Agent built without the CLI
        with (
            mock.patch.object(compat, "problems", return_value=["dspy.x is missing"]),
            self.assertRaisesRegex(RuntimeError, "dspy.x is missing"),
        ):
            scripted_agent(self, [])


if __name__ == "__main__":
    unittest.main()
