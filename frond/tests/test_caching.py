"""Prompt-cache behaviour of the per-step prompt, checked against Anthropic's documented cache rules.

The simulator below follows the rules in Anthropic's prompt-caching docs: a cache entry is a hash of the prefix
ending at a block marked with ``cache_control``; a request first looks up the hash at its breakpoint, then walks
backwards one block at a time, checking at most 20 positions (the breakpoint included), and reads the longest
prefix it finds; it then writes an entry at each of its breakpoints. Blocks are laid out tools, system, messages.
Sizes are counted in characters, which is enough to compare layouts.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import unittest
from dataclasses import dataclass, replace
from typing import Any

import dspy
from dspy._vendor.lm15.providers.anthropic import AnthropicLM
from dspy.lm15 import CacheConfig
from dspy.primitives.repl_types import REPLEntry, REPLHistory
from dspy.utils.exceptions import AdapterParseError

from frond.agent.adapter import FrondAdapter, last_reply_index
from frond.agent.scripted import Step
from tests.helpers import WorkspaceCase, scripted_agent

LOOKBACK = 20


@dataclass
class Turnout:
    read: int = 0
    written: int = 0
    uncached: int = 0


def blocks(payload: dict[str, Any]) -> list[tuple[str, bool]]:
    """(serialised block, carries cache_control) in Anthropic's prefix order."""
    out: list[tuple[str, bool]] = []
    system = payload.get("system")
    if isinstance(system, str):
        out.append((system, False))
    elif system:
        out.extend((block["text"], "cache_control" in block) for block in system)
    for message in payload["messages"]:
        content = message["content"]
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        for block in content:
            body = {k: v for k, v in block.items() if k != "cache_control"}
            out.append((message["role"] + json.dumps(body, sort_keys=True), "cache_control" in block))
    return out


class AnthropicCache:
    def __init__(self) -> None:
        self.entries: set[str] = set()

    def send(self, payload: dict[str, Any]) -> Turnout:
        laid_out = blocks(payload)
        hashes, sizes, total = [], [], 0
        running = hashlib.sha256()
        for text, _marked in laid_out:
            running.update(text.encode())
            hashes.append(running.copy().hexdigest())
            total += len(text)
            sizes.append(total)
        marks = [i for i, (_, marked) in enumerate(laid_out) if marked]
        hit = -1
        for mark in marks:
            for i in range(mark, max(-1, mark - LOOKBACK), -1):
                if hashes[i] in self.entries:
                    hit = max(hit, i)
                    break
        read = sizes[hit] if hit >= 0 else 0
        cached_end = sizes[marks[-1]] if marks else 0
        for mark in marks:
            self.entries.add(hashes[mark])
        return Turnout(read=read, written=max(0, cached_end - read), uncached=total - max(cached_end, read))


def anthropic_payload(request) -> dict[str, Any]:
    provider = AnthropicLM(api_key="test-key")
    return provider._payload(replace(request, model="claude-sonnet-5-5"), False)


class CacheLayoutTest(WorkspaceCase):
    files = {"app.py": "".join(f"line {i}\n" for i in range(400))}  # noqa: RUF012

    def run_turn(self, adapter: dspy.ChatAdapter, steps: int = 10) -> list[Turnout]:
        script = [Step(f"look {i}", f"print(view('app.py', {1 + (i % 9) * 40}))") for i in range(steps)]
        script.append(Step("done", 'SUBMIT("""finished""")'))
        agent, engine = scripted_agent(self, script, max_steps=steps + 2)
        agent.lm.kwargs["prompt_cache"] = CacheConfig(mode="auto")  # what build_lm configures for real providers
        agent.adapter = adapter
        agent.run_turn("read app.py")
        cache = AnthropicCache()
        requests = [r for r in engine.requests if r.messages]
        self.assertEqual(len(requests), steps + 1)
        return [cache.send(anthropic_payload(r)) for r in requests]

    @staticmethod
    def cost(turnouts: list[Turnout]) -> float:
        """Anthropic's multipliers on the base input price: writes 1.25x, reads 0.1x (0.05x on some models)."""
        return sum(1.25 * t.written + t.uncached + 0.1 * t.read for t in turnouts)

    def test_history_is_read_from_the_cache_on_every_later_step(self):
        before = self.run_turn(dspy.ChatAdapter())
        after = self.run_turn(FrondAdapter(cache_breakpoints=True))
        # One user message holding the whole history: only the system prompt is ever read back.
        system_only = before[1].read
        self.assertTrue(all(t.read == system_only for t in before[1:]))
        # As turns, each step reads everything up to its previous reply, so reads grow with the history.
        reads = [t.read for t in after]
        self.assertEqual(reads[0], 0)
        self.assertTrue(all(b > a for a, b in itertools.pairwise(reads[1:])), reads)
        share = sum(reads) / sum(t.read + t.written + t.uncached for t in after)
        self.assertGreater(share, 0.7)
        self.assertLess(self.cost(after), 0.6 * self.cost(before), (self.cost(before), self.cost(after)))

    def test_the_chat_layout_is_dspys_own(self):
        """H6's control arm: the history inside one user message, cached as DSPy alone would cache it (with
        DSPy's own field markers; the json protocol changes the reply format, not the layout)."""
        stock = self.run_turn(dspy.ChatAdapter(), steps=4)
        chat = self.run_turn(FrondAdapter(cache_breakpoints=True, layout="chat", protocol="markers"), steps=4)
        self.assertEqual(chat, stock)
        with self.assertRaises(ValueError):
            FrondAdapter(layout="scroll")

    def test_the_breakpoint_lands_on_the_latest_reply(self):
        steps = [Step("one", "print(1)"), Step("two", "print(2)"), Step("done", 'SUBMIT("""ok""")')]
        agent, engine = scripted_agent(self, steps)
        agent.adapter = FrondAdapter(cache_breakpoints=True)
        agent.run_turn("count")
        last = anthropic_payload(engine.requests[-1])
        marked = [m["role"] for m in last["messages"] if any("cache_control" in b for b in m["content"])]
        self.assertEqual(marked, ["assistant"])
        self.assertIn("cache_control", last["system"][0])
        self.assertEqual([m["role"] for m in last["messages"]], ["user", "assistant", "user", "assistant", "user"])


class AdapterFormatTest(unittest.TestCase):
    def test_earlier_steps_become_turns_and_the_volatile_fields_come_last(self):
        from frond.agent.prompts import CodingTurn
        from frond.agent.rlm import FrondRLM

        rlm = FrondRLM(CodingTurn)
        signature = rlm._action_signature_for_current_factory(None, "")
        history = REPLHistory(
            entries=[
                REPLEntry(reasoning="r1", code="print(1)", output="1\n"),
                REPLEntry(reasoning="r2", code="x = 2", output=""),
            ]
        )
        inputs = {"variables_info": ["Variable: `request`"], "repl_history": history, "iteration": "3/10"}
        adapter = FrondAdapter(protocol="markers")
        messages = adapter.format(signature, [], inputs)
        self.assertEqual([m["role"] for m in messages], ["system", "user", "assistant", "user", "assistant", "user"])
        self.assertIn("[[ ## variables_info ## ]]", messages[1]["content"])
        self.assertNotIn("[[ ## iteration ## ]]", messages[1]["content"])
        self.assertIn("[[ ## code ## ]]\n```python\nprint(1)\n```", messages[2]["content"])
        self.assertTrue(messages[3]["content"].startswith("=== Step 1 output ===\nOutput (2 chars):\n1"))
        self.assertIn("[[ ## iteration ## ]]\n3/10", messages[-1]["content"])
        self.assertNotIn("[[ ## iteration ## ]]", messages[3]["content"])
        self.assertEqual(last_reply_index([], history), 3)  # user, reply, output, reply (system excluded)

    def test_json_steps_are_json_turns_held_to_a_schema(self):  # D53
        from frond.agent.adapter import step_schema
        from frond.agent.prompts import CodingTurn
        from frond.agent.rlm import FrondRLM

        signature = FrondRLM(CodingTurn)._action_signature_for_current_factory(None, "")
        history = REPLHistory(entries=[REPLEntry(reasoning="r1", code="print(1)", output="1\n")])
        inputs = {"variables_info": ["Variable: `request`"], "repl_history": history, "iteration": "2/10"}
        adapter = FrondAdapter()
        messages = adapter.format(signature, [], inputs)
        self.assertEqual(json.loads(messages[2]["content"]), {"note": "r1", "code": "print(1)"})
        self.assertNotIn("[[ ## completed ## ]]", messages[0]["content"])
        self.assertNotIn("```python", messages[0]["content"])  # DSPy's desc of `code` asks for a fenced block
        self.assertTrue(
            messages[-1]["content"].endswith("Respond with one JSON object with the fields `note`, then `code`.")
        )
        schema = step_schema(signature).model_json_schema()
        self.assertEqual((set(schema["properties"]), schema["additionalProperties"]), ({"note", "code"}, False))
        self.assertEqual(adapter.parse(signature, '{"note": "n", "code": "x = 1"}'), {"note": "n", "code": "x = 1"})
        for bad in ('{"note": "n", "code": "x = ', '{"note": "n"}', "[[ ## note ## ]]\nn"):
            with self.subTest(bad=bad), self.assertRaises(AdapterParseError):
                adapter.parse(signature, bad)
        # Before any step there is nothing to lay out as turns: the ChatAdapter's own format is used.
        empty = adapter.format(signature, [], {**inputs, "repl_history": REPLHistory()})
        self.assertEqual([m["role"] for m in empty], ["system", "user"])


if __name__ == "__main__":
    unittest.main()
