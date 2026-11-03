"""The tool-calling arm (B8, H1): one tool call per step, with the same tools, prompt layout and harness."""

from __future__ import annotations

import unittest
from typing import ClassVar

from dspy.lm15 import CacheConfig

from frond.agent.adapter import FrondAdapter
from frond.agent.scripted import ToolStep
from frond.events import FileChanged
from tests.helpers import WorkspaceCase, scripted_agent
from tests.test_caching import anthropic_payload


def text_of(request) -> str:
    return "\n".join(m.text or "" for m in request.messages)


class ToolsArmTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {"app.py": "def f():\n    return 1\n"}

    def test_a_turn_of_single_tool_calls_fixes_and_answers(self):
        steps = [
            ToolStep("Look.", "view", {"path": "app.py"}),
            ToolStep("Fix.", "edit", {"path": "app.py", "old": "return 1", "new": "return 2"}),
            ToolStep("Check.", "sh", {"command": "python3 -c 'import app; print(app.f())'"}),
            ToolStep("Done.", "submit", {"response": "f now returns 2"}),
        ]
        agent, engine = scripted_agent(self, steps, arm="react")
        record = agent.run_turn("make f return 2")
        self.assertEqual(record.response, "f now returns 2")
        self.assertEqual((self.root / "app.py").read_text(), "def f():\n    return 2\n")
        self.assertEqual([e.path for e in self.of_type(FileChanged)], ["app.py"])
        last = text_of(engine.requests[3])
        self.assertIn("[[ ## tool ## ]]\nview", last)  # earlier calls are turns in the tool-call format
        self.assertIn('[[ ## args ## ]]\n{"path": "app.py"}', last)
        self.assertIn("exit code 0\n2", last)  # the command's result, as printing it would show
        system = engine.requests[0].system or ""
        system = system if isinstance(system, str) else "".join(getattr(p, "text", "") for p in system)
        self.assertIn("- submit(response: str)", system)
        self.assertIn("- edit(", system)
        self.assertNotIn("[[ ## code ## ]]", system + last)  # no code anywhere: the model cannot write any
        self.assertNotIn("repl_variables", system + last)
        steps_logged = [r.code for r in agent.steps.records() if r.kind == "step"]
        self.assertEqual(steps_logged[0], "view(path='app.py')")

    def test_unknown_tools_and_bad_arguments_are_errors_the_model_sees(self):
        steps = [
            ToolStep("Try.", "teleport", {}),
            ToolStep("Try again.", "view", {"nope": 1}),
            ToolStep("Done.", "submit", {"response": "ok"}),
        ]
        agent, engine = scripted_agent(self, steps, arm="react")
        agent.run_turn("go")
        second, third = text_of(engine.requests[1]), text_of(engine.requests[2])
        self.assertIn("There is no tool named 'teleport'", second)
        self.assertIn("[Error]", third)

    def test_the_cache_mark_lands_on_the_latest_tool_call(self):
        steps = [
            ToolStep("One.", "ls", {}),
            ToolStep("Two.", "view", {"path": "app.py"}),
            ToolStep("Done.", "submit", {"response": "ok"}),
        ]
        agent, engine = scripted_agent(self, steps, arm="react")
        agent.lm.kwargs["prompt_cache"] = CacheConfig(mode="auto")
        assert isinstance(agent.adapter, FrondAdapter)
        agent.adapter.cache_breakpoints = True
        agent.run_turn("go")
        last = anthropic_payload(engine.requests[-1])
        marked = [m["role"] for m in last["messages"] if any("cache_control" in b for b in m["content"])]
        self.assertEqual(marked, ["assistant"])
        self.assertEqual([m["role"] for m in last["messages"]], ["user", "assistant", "user", "assistant", "user"])


if __name__ == "__main__":
    unittest.main()
