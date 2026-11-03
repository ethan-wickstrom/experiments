"""Scopes as savepoints (B9, H5): a closed scope collapses to goal and result, an abandoned one rewinds the workspace
and the context with a note, and the prompt prefix before a scope is never rewritten."""

from __future__ import annotations

import unittest
from typing import ClassVar

from frond.agent.scripted import Step
from tests.helpers import WorkspaceCase, scripted_agent


def prompts_of(engine) -> list[str]:
    return ["\n".join(m.text or "" for m in r.messages) for r in engine.requests if r.messages]


class ScopesTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {"app.py": "x = 1\n"}

    def test_a_closed_scope_becomes_goal_and_result(self):
        steps = [
            Step("Before.", "print('before the scope')"),
            Step("Open.", "open_scope('inspect the module')"),
            Step("Dig.", "print('detail ' * 50)"),
            Step("Close.", "close_scope('found that x is 1')"),
            Step("Done.", "SUBMIT(response='ok')"),
        ]
        agent, engine = scripted_agent(self, steps, scopes=True)
        agent.run_turn("go")
        prompts = prompts_of(engine)
        last = prompts[-1]
        self.assertIn("Scope closed: inspect the module\nResult: found that x is 1", last)
        self.assertNotIn("detail detail", last)  # the scope's steps are gone from the context...
        self.assertTrue(any("detail detail" in r.output for r in agent.steps.records()))  # ...not from the log
        self.assertIn("before the scope", last)  # what came before the scope stays
        self.assertIn("[[ ## open_scopes ## ]]\n1. inspect the module (opened at step 2)", prompts[2])
        self.assertIn("[[ ## open_scopes ## ]]\n(none)", last)
        self.assertEqual((agent.scopes.opened, agent.scopes.closed), (1, 1))

    def test_an_abandoned_scope_rewinds_the_workspace_and_the_context(self):
        steps = [
            Step("Open.", "open_scope('try rewriting app.py')\ny = 5"),
            Step("Try.", "edit('app.py', 'x = 1', 'x = 99')\nwrite('scratch.py', 'tmp')"),
            Step("Give up.", "abandon_scope('the rewrite breaks the import')"),
            Step("Done.", "import os\nSUBMIT(response=open('app.py').read() + str(os.path.exists('scratch.py')))"),
        ]
        agent, engine = scripted_agent(self, steps, scopes=True)
        record = agent.run_turn("go")
        self.assertEqual(record.response, "x = 1\nFalse")
        last = prompts_of(engine)[-1]
        self.assertIn("Abandoned: try rewriting app.py\nWhy: the rewrite breaks the import", last)
        self.assertIn("Reverted: app.py, scratch.py", last)
        self.assertIn("now stale: y", last)
        self.assertNotIn("x = 99", last)

    def test_abandoning_reverts_what_the_opening_step_did_before_it_opened(self):  # Devin, #18 (F38)
        steps = [
            Step("Edit, then open.", "edit('app.py', 'x = 1', 'x = 2')\nopen_scope('try it')"),
            Step("Give up.", "abandon_scope('wrong idea')"),
            Step("Done.", "SUBMIT(response=open('app.py').read())"),
        ]
        agent, engine = scripted_agent(self, steps, scopes=True)
        record = agent.run_turn("go")
        self.assertEqual(record.response, "x = 1")  # the opening step left the context, and so did its edit
        self.assertIn("Reverted: app.py", prompts_of(engine)[-1])

    def test_without_snapshots_a_scope_cannot_be_abandoned_only_closed(self):  # Devin, #18 (F39)
        steps = [
            Step("Open.", "open_scope('try it')"),
            Step("Try.", "write('scratch.py', 'tmp')"),
            Step("Give up.", "abandon_scope('wrong idea')"),
            Step("Close instead.", "close_scope('failed: wrote scratch.py')"),
            Step("Done.", "SUBMIT(response='ok')"),
        ]
        agent, engine = scripted_agent(self, steps, scopes=True, worlds=False)
        agent.run_turn("go")
        prompts = prompts_of(engine)
        self.assertIn("this scope cannot be abandoned", prompts[3])
        self.assertTrue((self.root / "scratch.py").exists())
        self.assertNotIn("Abandoned: try it", prompts[-1])  # the attempt was not cut from the context
        self.assertIn("Scope closed: try it\nResult: failed: wrote scratch.py", prompts[-1])

    def test_files_that_could_not_be_reverted_are_named(self):  # Devin, #18 (F40)
        (self.root / "data.bin").write_bytes(b"0" * 4000)
        steps = [
            Step("Open.", "open_scope('try it')"),
            Step("Try.", "sh('printf changed > data.bin')"),
            Step("Give up.", "abandon_scope('wrong idea')"),
            Step("Done.", "SUBMIT(response='ok')"),
        ]
        agent, engine = scripted_agent(self, steps, scopes=True)
        assert agent.timeline is not None
        agent.timeline.work.max_blob = 1000
        agent.run_turn("go")
        self.assertIn(
            "Still changed, since they were too large or unreadable to have been kept: data.bin", prompts_of(engine)[-1]
        )

    def test_the_prompt_prefix_before_a_scope_is_unchanged(self):
        steps = [
            Step("Before.", "print('before')"),
            Step("Open.", "open_scope('work')"),
            Step("Work.", "print('inside')"),
            Step("Close.", "close_scope('done')"),
            Step("Done.", "SUBMIT(response='ok')"),
        ]
        agent, engine = scripted_agent(self, steps, scopes=True)
        agent.run_turn("go")
        before_close = [m.text for m in engine.requests[2].messages]  # the prompt of the step that opened...
        after_close = [m.text for m in engine.requests[4].messages]
        shared = 3  # the first message and the "before" step's reply: up to where the scope began
        self.assertEqual(before_close[:shared], after_close[:shared])

    def test_ending_a_scope_that_is_not_open_is_an_error_the_model_sees(self):
        steps = [Step("Close.", "close_scope('nothing')"), Step("Done.", "SUBMIT(response='ok')")]
        agent, engine = scripted_agent(self, steps, scopes=True)
        agent.run_turn("go")
        self.assertIn("there is no open scope", prompts_of(engine)[1])

    def test_with_scopes_off_there_are_no_scope_tools_or_field(self):
        steps = [Step("Open.", "open_scope('x')"), Step("Done.", "SUBMIT(response='ok')")]
        agent, engine = scripted_agent(self, steps)
        agent.run_turn("go")
        prompts = prompts_of(engine)
        self.assertIn("NameError", prompts[1])
        self.assertTrue(all("open_scopes" not in p for p in prompts))


if __name__ == "__main__":
    unittest.main()
