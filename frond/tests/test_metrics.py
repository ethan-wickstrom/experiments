"""What a run did, counted and exported for research (ledger B2)."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest import mock

import dspy
from dspy.utils.exceptions import AdapterParseError

from bench import analyze
from frond.agent.adapter import FrondAdapter
from frond.agent.lm import usage_totals
from frond.agent.metrics import RunMetrics, normalize_usage
from frond.agent.prompts import CodingTurn
from frond.agent.rlm import FrondRLM
from frond.agent.scripted import CutOff, Step, ToolStep
from frond.cli import export_run
from tests.helpers import WorkspaceCase, scripted_agent


class NormalizeUsageTest(unittest.TestCase):
    def test_anthropic_counts_cache_outside_input_tokens(self):
        raw = {
            "input_tokens": 200,
            "cache_read_input_tokens": 9000,
            "cache_creation_input_tokens": 800,
            "output_tokens": 300,
        }
        self.assertEqual(
            normalize_usage(raw),
            {"input": 10_000, "cache_read": 9000, "cache_write": 800, "output": 300, "reasoning": 0},
        )

    def test_openai_style_usage_already_includes_cached_tokens(self):
        raw = {
            "prompt_tokens": 10_000,
            "completion_tokens": 300,
            "prompt_tokens_details": {"cached_tokens": 9000},
            "completion_tokens_details": {"reasoning_tokens": 120},
        }
        self.assertEqual(
            normalize_usage(raw),
            {"input": 10_000, "cache_read": 9000, "cache_write": 0, "output": 300, "reasoning": 120},
        )


class ParseFailureTest(unittest.TestCase):
    def test_a_reply_that_does_not_parse_is_counted(self):
        metrics = RunMetrics()
        signature = FrondRLM(CodingTurn)._action_signature_for_current_factory(None, "")
        with self.assertRaises(AdapterParseError):
            FrondAdapter(metrics=metrics).parse(signature, "no field markers at all")
        self.assertEqual(metrics.parse_failures, 1)

    def signature(self, action_space: str = "code") -> type[dspy.Signature]:
        rlm = FrondRLM(CodingTurn, action_space=action_space)
        return rlm._tool_signature() if action_space == "tools" else rlm._action_signature_for_current_factory(None, "")

    def test_a_reply_off_the_protocol_that_says_what_to_run_is_recovered(self):  # G34: Opus 5.5's two shapes
        fenced = (
            "I'll start by looking at the renderer.\n\n```python\nprint(ls('.'))\nr = sh('ls')\n```\n\n"
            "[[ ## completed ## ]]\n"
        )
        invoke = (
            'I have three steps, so this one gathers everything.\n\n\n<invoke name="python">\n'
            "<parameter name=\"code\">print(read('/app/render.py')[:6000])\nprint(ls('/app/data'))</parameter>\n"
            "</invoke>\n\n[[ ## completed ## ]] \n"
        )
        metrics = RunMetrics()
        adapter = FrondAdapter(metrics=metrics)
        got = adapter.parse(self.signature(), fenced)
        self.assertEqual(got["note"], "I'll start by looking at the renderer.")
        self.assertEqual(got["code"], "```python\nprint(ls('.'))\nr = sh('ls')\n```")
        got = adapter.parse(self.signature(), invoke)
        self.assertEqual(got["note"], "I have three steps, so this one gathers everything.")
        self.assertEqual(got["code"], "```python\nprint(read('/app/render.py')[:6000])\nprint(ls('/app/data'))\n```")
        tool = '<invoke name="view">\n<parameter name="path">app.py</parameter>\n<parameter name="start">3</parameter>'
        got = adapter.parse(self.signature("tools"), f"Look first.\n{tool}\n</invoke>")
        self.assertEqual(got, {"note": "Look first.", "tool": "view", "args": {"path": "app.py", "start": 3}})
        self.assertEqual((metrics.parse_failures, metrics.parse_recovered), (3, 3))  # adherence is still measured

    def test_a_reply_that_could_mean_more_than_one_action_is_not_guessed(self):  # G34
        metrics = RunMetrics()
        adapter = FrondAdapter(metrics=metrics)
        replies = [
            "First:\n```python\nprint(1)\n```\nthen:\n```python\nprint(2)\n```",
            '<invoke name="python"><parameter name="script">print(1)</parameter></invoke>',
            '<invoke name="a"><parameter name="code">1</parameter></invoke><invoke name="b"></invoke>',
            "```bash\nls\n```",
            # Codex, #27: a fenced action and an invoked one; running only the second would drop the first
            'Read it:\n```python\nread("app.py")\n```\n<invoke name="python"><parameter name="code">'
            'write("app.py", "x")</parameter></invoke>',
            # Devin, #27 (F50): a repeated parameter, and text in the call that is no parameter, could hide an action
            '<invoke name="python"><parameter name="code">write("a", "1")</parameter>'
            '<parameter name="code">write("b", "2")</parameter></invoke>',
            '<invoke name="python">write("a", "1")<parameter name="code">print(1)</parameter></invoke>',
        ]
        for reply in replies:
            with self.assertRaises(AdapterParseError, msg=reply):
                adapter.parse(self.signature(), reply)
        self.assertEqual((metrics.parse_failures, metrics.parse_recovered), (7, 0))


class NoteFieldTest(WorkspaceCase):
    """No prompt asks for the model's reasoning in its reply: Sonnet 5.5's classifier refused every step that did, as
    reasoning extraction, and Anthropic's guidance is a short explanation instead (G41, D51)."""

    def test_both_arms_ask_for_a_note_and_never_for_reasoning(self):
        done: list[tuple[str, Step | ToolStep]] = [
            ("rlm", Step("Done.", "SUBMIT(response='ok')")),
            ("react", ToolStep("Done.", "submit", {"response": "ok"})),
        ]
        for arm, step in done:
            with self.subTest(arm=arm):
                agent, engine = scripted_agent(self, [step], arm=arm)
                record = agent.run_turn("go")
                self.assertEqual(record.response, "ok")
                request = engine.requests[0]
                system = (
                    request.system
                    if isinstance(request.system, str)
                    else "".join(getattr(part, "text", "") for part in request.system or [])
                )
                text = system + "\n".join(m.text or "" for m in request.messages)
                self.assertIn("[[ ## note ## ]]", text)
                self.assertNotIn("## reasoning ##", text)
                self.assertNotIn("Think step-by-step", text)
                self.assertNotIn("`reasoning`", text)


class RefusalTest(WorkspaceCase):
    def test_a_provider_refusal_ends_the_turn_as_the_providers_failure(self):  # G43: not 40 billed retries
        from types import SimpleNamespace

        refusal = SimpleNamespace(provider_data={"stop_details": {"category": "reasoning_extraction"}})
        agent, engine = scripted_agent(self, ["", Step("Never reached.", "SUBMIT(response='ok')")])
        with mock.patch("frond.agent.rlm._call_of", return_value=("content_filter", refusal)):
            record = agent.run_turn("go")
        self.assertEqual((record.status, record.error_kind), ("error", "provider"))
        self.assertEqual(agent.metrics.refusal, "reasoning_extraction")
        self.assertEqual(len(engine.requests), 1)


class FenceTest(WorkspaceCase):
    def test_an_answer_with_a_code_block_is_not_cut_at_its_inner_fence(self):  # G42: seen on Opus, Sonnet and Haiku
        answer = "app.py holds one line:\n\n```python\nx = 1\n```\n\nNothing else."
        agent, _ = scripted_agent(self, [Step("Answer.", f"SUBMIT(response={answer!r})")])
        record = agent.run_turn("go")
        self.assertEqual((record.status, record.response), ("done", answer))

    def test_other_shapes_still_go_to_dspy(self):
        from frond.agent.rlm import strip_fences

        self.assertEqual(strip_fences("print(1)"), "print(1)")
        self.assertEqual(strip_fences("```py\nprint(1)\n```"), "print(1)")
        with self.assertRaises(SyntaxError):
            strip_fences("```bash\nls\n```")


class UnparsedStepTest(WorkspaceCase):
    """A reply frond cannot read costs a step and is shown to the model; it no longer ends the run (G34)."""

    def test_the_turn_goes_on_after_a_reply_that_cannot_be_read(self):
        done_steps: list[tuple[str, Step | ToolStep]] = [
            ("rlm", Step("Done.", "SUBMIT(response='ok')")),
            ("react", ToolStep("Done.", "submit", {"response": "ok"})),
        ]
        for arm, done in done_steps:
            with self.subTest(arm=arm):
                agent, engine = scripted_agent(self, ["Let me think about this first.", done], arm=arm)
                record = agent.run_turn("go")
                self.assertEqual((record.status, record.response), ("done", "ok"))
                self.assertEqual((agent.metrics.parse_failures, agent.metrics.unparsed_steps), (1, 1))
                second = "\n".join(m.text or "" for m in engine.requests[1].messages)
                self.assertIn("did not follow the step format", second)
                self.assertIn("Let me think about this first.", second)  # its own words, in the right format

    def test_a_reply_cut_off_at_the_output_limit_is_named_as_such(self):  # G38
        steps: list[Step | ToolStep | CutOff | str] = [
            CutOff("I'll write the whole solver now:\n```python\nfor i in range(10"),  # stopped mid-block
            Step("Smaller.", "SUBMIT(response='ok')"),
        ]
        agent, engine = scripted_agent(self, steps)
        record = agent.run_turn("go")
        self.assertEqual((record.status, record.response), ("done", "ok"))
        second = "\n".join(m.text or "" for m in engine.requests[1].messages)
        self.assertIn("reached the output limit and was cut off", second)
        self.assertNotIn("did not follow the step format", second)
        self.assertEqual((agent.metrics.unparsed_steps, agent.metrics.cut_off_replies), (1, 1))

    def test_a_cut_off_is_read_from_either_response_shape(self):  # Codex, #31: the LiteLLM route's choices
        from types import SimpleNamespace

        from frond.agent.rlm import _finish_reason

        self.assertEqual(_finish_reason(SimpleNamespace(finish_reason="length"), 0), "length")
        litellm = SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop"), {"finish_reason": "length"}])
        self.assertEqual(_finish_reason(litellm, 1), "length")
        self.assertIsNone(_finish_reason(None, 0))

    def test_a_sub_agents_replies_count_apart_from_the_main_models(self):  # Devin, #27 (F51): another model
        steps: list[Step | ToolStep | str] = [
            Step("Delegate.", "print(subagent('look around'))"),
            "Let me check.",  # the sub-agent's first reply: nothing to run
            "Looking now:\n```python\nprint(1)\n```",  # recovered
            Step("The sub-agent reports.", "SUBMIT(report='seen')"),
            Step("Done.", "SUBMIT(response='ok')"),
        ]
        agent, _ = scripted_agent(self, steps)
        record = agent.run_turn("go")
        self.assertEqual((record.status, record.response), ("done", "ok"))
        counts = agent.metrics.as_dict()
        self.assertEqual((counts["parse_failures"], counts["parse_recovered"], counts["unparsed_steps"]), (0, 0, 0))
        sub = (counts["sub_parse_failures"], counts["sub_parse_recovered"], counts["sub_unparsed_steps"])
        self.assertEqual(sub, (2, 1, 1))


class UsageTotalsTest(unittest.TestCase):
    def test_every_provider_shape_is_counted(self):
        anthropic = SimpleNamespace(
            history=[
                {
                    "usage": {
                        "input_tokens": 200,
                        "cache_read_input_tokens": 9000,
                        "cache_creation_input_tokens": 800,
                        "output_tokens": 300,
                    },
                    "cost": 0.01,
                }
            ]
        )
        openai = SimpleNamespace(
            history=[
                {
                    "usage": {
                        "prompt_tokens": 1000,
                        "prompt_tokens_details": {"cached_tokens": 600},
                        "completion_tokens": 50,
                        "completion_tokens_details": {"reasoning_tokens": 20},
                    },
                    "cost": 0.002,
                }
            ]
        )
        totals = usage_totals(cast(Any, anthropic), cast(Any, openai), cast(Any, anthropic))  # each LM counted once
        self.assertEqual(
            totals,
            {
                "calls": 2,
                "input_tokens": 11_000,
                "cache_read_tokens": 9_600,
                "cache_write_tokens": 800,
                "output_tokens": 350,
                "reasoning_tokens": 20,
                "cost_usd": 0.012,
            },
        )


class ExportTest(WorkspaceCase):
    files = {"notes.txt": "hello\n"}  # noqa: RUF012

    def test_the_export_counts_syntax_errors_tool_calls_and_failed_edits(self):
        steps = [
            Step("broken", "def broken(:"),
            Step("edit a missing file", "edit('missing.txt', 'a', 'b')"),
            Step("edit for real", "edit('notes.txt', 'hello', 'goodbye')"),
            Step("done", "SUBMIT(response='done')"),
        ]
        agent, _ = scripted_agent(self, steps)
        agent.run_turn("tidy the notes")
        out = Path(tempfile.mkdtemp(prefix="frond-export-"))
        self.addCleanup(shutil.rmtree, out, True)
        export_run(agent, out)
        metrics = json.loads((out / "metrics.json").read_text())
        self.assertEqual(metrics["syntax_errors"], 1)
        self.assertEqual(metrics["tool_calls"]["edit"], 2)
        self.assertEqual(metrics["tool_failures"], {"edit": 1})
        self.assertEqual(metrics["failed_edits"], 1)
        self.assertEqual((metrics["turns"], metrics["steps"]), (1, 4))
        self.assertEqual(metrics["config"]["layout"], "turns")
        calls = [json.loads(line) for line in (out / "calls.jsonl").read_text().splitlines()]
        self.assertTrue(calls)
        self.assertTrue(all({"role", "model", "usage", "raw_usage"} <= set(c) for c in calls))


class ProviderFailureTest(WorkspaceCase):
    """A run that ends because the model provider failed is flagged, exits 75, and is not scored (ledger G22)."""

    def test_a_rate_limit_is_the_providers_failure_not_the_agents(self):
        agent, engine = scripted_agent(self, [Step("Go.", "print(1)")])
        with mock.patch.object(engine, "_completion", side_effect=dspy.LMRateLimitError("too many requests")):
            record = agent.run_turn("go")
        self.assertEqual((record.status, record.error_kind), ("error", "provider"))
        out = Path(tempfile.mkdtemp(prefix="frond-export-"))
        self.addCleanup(shutil.rmtree, out, True)
        export_run(agent, out)
        metrics = json.loads((out / "metrics.json").read_text())
        self.assertEqual(metrics["error_kind"], "provider")
        trial = out.parent / (out.name + "-trial")
        self.addCleanup(shutil.rmtree, trial, True)
        (trial / "agent").mkdir(parents=True)
        shutil.copytree(out, trial / "agent" / "frond")
        started = {"started_at": "2026-11-03T10:00:00Z", "finished_at": "2026-11-03T10:01:00Z"}
        (trial / "result.json").write_text(
            json.dumps(
                {"task_id": {"name": "t"}, "agent_execution": started, "verifier_result": {"rewards": {"reward": 0}}}
            )
        )
        scored = analyze.load_trial(trial, "frond", analyze.load_prices())
        assert scored is not None
        self.assertIsNone(scored.reward)  # reported as an infrastructure failure, never scored
        self.assertEqual(scored.exception, "provider failure")

    def test_a_provider_failure_the_turn_survives_is_counted(self):  # F47
        steps = [
            Step("Ask.", "try:\n    llm_query('hi')\nexcept Exception as exc:\n    print('failed:', exc)"),
            Step("Done.", "SUBMIT(response='ok')"),
        ]

        def refuse(prompt: str) -> str:
            raise dspy.LMRateLimitError("too many requests")

        agent, _ = scripted_agent(self, steps, sub_answer=refuse)
        record = agent.run_turn("go")
        self.assertEqual((record.status, record.response), ("done", "ok"))  # still the agent's run, and scored
        self.assertEqual(agent.metrics.provider_errors, 1)
        self.assertEqual(agent.metrics.as_dict()["provider_errors"], 1)

    def test_a_sub_agents_provider_failure_is_counted_once(self):  # Devin, #23
        agent, _ = scripted_agent(self, [Step("Done.", "SUBMIT(response='ok')")])
        counted = dspy.LMRateLimitError("already counted by llm_query")
        counted.frond_counted = True  # ty: ignore[unresolved-attribute]
        for error, expected in ((counted, 0), (dspy.LMRateLimitError("its own call"), 1)):
            with (
                mock.patch("frond.agent.session.FrondRLM.__call__", side_effect=error),
                self.assertRaisesRegex(RuntimeError, "sub-agent failed"),
            ):
                agent._run_subagent("look")
            self.assertEqual(agent.metrics.provider_errors, expected)

    def test_an_agent_error_stays_the_agents(self):
        agent, engine = scripted_agent(self, [Step("Go.", "print(1)")])
        with mock.patch.object(engine, "_completion", side_effect=ValueError("bad output")):
            record = agent.run_turn("go")
        self.assertEqual(record.status, "error")
        self.assertNotIn(record.error_kind, ("", "provider"))  # scored as the agent's failure


if __name__ == "__main__":
    unittest.main()
