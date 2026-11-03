"""The tool-calling arm (B8, H1): one tool call per step, with the same tools, prompt layout and harness."""

from __future__ import annotations

import json
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
        self.assertRegex(
            last, r"\$ python3 -c 'import app; print\(app.f\(\)\)'  \[exit 0, [\d.]+s\]\n2"
        )  # as in the REPL
        system = engine.requests[0].system or ""
        system = system if isinstance(system, str) else "".join(getattr(p, "text", "") for p in system)
        self.assertIn("- submit(response: str)", system)
        self.assertIn("- edit(", system)
        self.assertNotIn("[[ ## code ## ]]", system + last)  # no code anywhere: the model cannot write any
        self.assertNotIn("repl_variables", system + last)
        steps_logged = [r.code for r in agent.steps.records() if r.kind == "step"]
        self.assertEqual(json.loads(steps_logged[0]), {"tool": "view", "args": {"path": "app.py"}})  # F35

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

    def test_a_background_job_shows_the_id_its_tools_take(self):  # Devin, #16 (F33)
        steps = [
            ToolStep("Start it.", "sh", {"command": "sleep 30", "background": True}),
            ToolStep("Stop it.", "job_kill", {"job": 1}),
            ToolStep("Done.", "submit", {"response": "ok"}),
        ]
        agent, engine = scripted_agent(self, steps, arm="react")
        agent.run_turn("go")
        self.assertRegex(text_of(engine.requests[1]), r"job 1 \(pid \d+\) running; log: ")

    def test_grep_matches_print_as_in_the_repl(self):  # Devin, #16 (F36)
        steps = [ToolStep("Find.", "grep", {"pattern": "return"}), ToolStep("Done.", "submit", {"response": "ok"})]
        agent, engine = scripted_agent(self, steps, arm="react")
        agent.run_turn("go")
        second = text_of(engine.requests[1])
        self.assertIn("app.py\n  2:     return 1", second)
        self.assertIn("(1 matches in 1 files)", second)
        self.assertNotIn('"__frond__"', second)

    def test_a_submit_with_the_wrong_arguments_is_an_error_the_model_sees(self):  # Devin, #16 (F34)
        steps = [
            ToolStep("Done?", "submit", {"respose": "typo"}),
            ToolStep("Done.", "submit", {"response": "ok"}),
        ]
        agent, engine = scripted_agent(self, steps, arm="react")
        record = agent.run_turn("go")
        self.assertEqual(record.response, "ok")
        self.assertIn("submit takes exactly these arguments: response; it got: respose", text_of(engine.requests[1]))

    def test_earlier_user_requests_survive_a_long_history(self):  # Devin, #16 (F32): as in the RLM arm
        steps = [
            ToolStep("Reply.", "submit", {"response": "x" * 20_000}),
            ToolStep("Done.", "submit", {"response": "ok"}),
        ]
        agent, engine = scripted_agent(self, steps, arm="react")
        agent.run_turn("Never edit migrations.")
        agent.run_turn("Now tidy app.py.")
        second_turn = text_of(engine.requests[-1])
        self.assertIn("Never edit migrations.", second_turn)
        self.assertIn("The user's messages so far, verbatim", second_turn)

    def test_a_cut_output_points_at_what_this_arm_can_do(self):  # Devin, #21 (F48)
        from frond.agent.adapter import narrowing_hint

        signature = agent_signature(self)
        hint = narrowing_hint(signature, 7, history_tools=True)
        self.assertNotIn("history_step", hint)
        self.assertIn("narrower range", hint)
        self.assertIn("sub-agent or fetch()", hint)  # Devin, #30 (F56): not every cut result is a file

    def test_the_scripted_playground_replays_tool_calls(self):  # Devin, #16 (F37)
        import contextlib
        import io

        from frond import cli

        script = self.root / "script.json"
        script.write_text(json.dumps([{"reasoning": "Done.", "tool": "submit", "args": {"response": "replayed"}}]))
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = cli.main(["-p", "--script", str(script), "--arm", "react", "--cwd", str(self.root), "go"])
        self.assertEqual(code, 0)
        self.assertIn("replayed", out.getvalue())
        err = io.StringIO()  # Devin, #30 (F55): a script of the other arm's shape is refused, not replayed as errors
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = cli.main(["-p", "--script", str(script), "--arm", "rlm", "--cwd", str(self.root), "go"])
        self.assertEqual(code, 2)
        self.assertIn("every script entry must be {reasoning, code}", err.getvalue())


def agent_signature(case: WorkspaceCase):
    agent, _ = scripted_agent(case, [], arm="react")
    return agent.rlm._tool_signature()


if __name__ == "__main__":
    unittest.main()
