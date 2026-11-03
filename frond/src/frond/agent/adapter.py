"""How each RLM step's prompt is laid out, so the provider's prompt cache can serve the history.

``dspy.RLM`` passes the REPL history as one input field, so every step sends a single, ever longer user
message. Providers cache prompts by prefix. Anthropic additionally caches only at blocks it has been told to
mark, and looks back at most 20 blocks from a mark, so on Claude none of a long history in one block was ever
read from the cache: every step paid full price for every earlier step.

``FrondAdapter`` keeps the ChatAdapter's text protocol (field markers, parsing, streaming) and changes only how
the history is sent. The model's own earlier replies become assistant messages, and each REPL output the user
message after its reply. Everything up to the latest reply is then byte-identical from one step to the next;
only the newest output and the step counter follow it. For Anthropic models the latest reply is also marked as a
cache breakpoint, so the next step reads everything before it from the cache.

Laying the history out as turns also gives the model its earlier replies in exactly the format it must produce,
and keeps tool output in messages of its own rather than in one string with the user's request.
"""

from __future__ import annotations

from typing import Any

import dspy
from dspy.adapters.base import _expand_legacy_custom_type_markers_in_chat_message
from dspy.lm15 import CacheConfig
from dspy.primitives.repl_types import REPLEntry, REPLHistory

VOLATILE = ("iteration", "repl_variables")  # change every step, so they go after the cached prefix
NOTE_CODE = "# folded"  # frond.agent.rlm.NOTE_CODE (not imported: rlm imports this module's users)
HISTORY_NOTE = (
    "Your earlier steps in this turn follow as conversation messages: each reply of yours, then the REPL's output "
    "for it."
)


def is_action(signature: type[dspy.Signature], inputs: dict[str, Any]) -> bool:
    """True for the RLM's per-step action call (as opposed to its extract fallback or a sub-query)."""
    return (
        "code" in signature.output_fields
        and "repl_history" in signature.input_fields
        and isinstance(inputs.get("repl_history"), REPLHistory)
    )


def last_reply_index(demos: list[dict[str, Any]], history: REPLHistory) -> int:
    """Index, among the messages after the system prompt, of the model's latest reply."""
    # demos come in (user, assistant) pairs, then the first user message, then one (reply, output) pair per step
    return 2 * len(demos) + 2 * len(history.entries) - 1


class FrondAdapter(dspy.ChatAdapter):
    def __init__(self, *, cache_breakpoints: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.cache_breakpoints = cache_breakpoints

    def __call__(
        self,
        lm: dspy.BaseLM,
        lm_kwargs: dict[str, Any],
        signature: type[dspy.Signature],
        demos: list[dict[str, Any]],
        inputs: dict[str, Any],
    ) -> list[dict[str, Any]]:
        history = inputs.get("repl_history")
        if (
            self.cache_breakpoints
            and isinstance(history, REPLHistory)
            and history.entries
            and is_action(signature, inputs)
        ):
            cache = CacheConfig(prefix_until_index=last_reply_index(demos, history))
            lm_kwargs = {**lm_kwargs, "prompt_cache": cache}
        return super().__call__(lm, lm_kwargs, signature, demos, inputs)

    def format(
        self,
        signature: type[dspy.Signature],
        demos: list[dict[str, Any]],
        inputs: dict[str, Any],
    ) -> list[dict[str, Any]]:
        history = inputs.get("repl_history")
        if not is_action(signature, inputs) or not isinstance(history, REPLHistory) or not history.entries:
            return super().format(signature, demos, inputs)
        context = {k: v for k, v in inputs.items() if k not in ("repl_history", *VOLATILE)}
        first = self.format_user_message_content(signature, context)
        messages: list[dict[str, Any]] = [{"role": "system", "content": self.format_system_message(signature)}]
        messages.extend(self.format_demos(signature, demos))
        messages.append({"role": "user", "content": f"{first}\n\n[[ ## repl_history ## ]]\n{HISTORY_NOTE}"})
        last = len(history.entries) - 1
        for i, entry in enumerate(history.entries):
            reply = {"reasoning": entry.reasoning, "code": f"```python\n{entry.code}\n```"}
            messages.append({"role": "assistant", "content": self.format_assistant_message_content(signature, reply)})
            title = "Folded steps" if entry.code == NOTE_CODE else f"Step {getattr(entry, 'step', 0) or i + 1} output"
            output = f"=== {title} ===\n{REPLEntry.format_output(entry.output, history.max_output_chars)}"
            if i == last:  # what changes every step goes after the cached prefix
                current = {k: v for k, v in inputs.items() if k in VOLATILE}
                output += "\n\n" + self.format_user_message_content(signature, current, main_request=True)
            messages.append({"role": "user", "content": output})
        return [_expand_legacy_custom_type_markers_in_chat_message(message) for message in messages]
