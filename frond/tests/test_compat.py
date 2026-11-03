"""An incompatible DSPy fails at startup with what changed (R9, B11)."""

from __future__ import annotations

import contextlib
import io
import unittest
from unittest import mock

from dspy.predict import rlm as dspy_rlm

from frond import cli
from frond.agent import compat


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


if __name__ == "__main__":
    unittest.main()
