"""What a run did, counted for research (ledger B2, research.md "Measurements per run").

Every model call keeps its provider-reported usage, raw as well as normalized, because cache accounting differs by
provider and the analysis may need fields nobody thought to extract. The counters cover how well the model follows
frond's protocol (replies that do not parse, code that does not compile) and how its tool calls fare. Failed edits are
the H3 and A6 signal.
"""

from __future__ import annotations

import functools
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunMetrics:
    parse_failures: int = 0  # replies that did not parse into the step's output fields
    syntax_errors: int = 0  # code that did not compile
    tool_calls: Counter[str] = field(default_factory=Counter)
    tool_failures: Counter[str] = field(default_factory=Counter)  # calls that raised: the model got an error back

    def counted(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        """``fn`` as a REPL tool that counts its calls and failures (signature and docs kept for the model)."""
        name = getattr(fn, "__name__", "tool")

        @functools.wraps(fn)
        def tool(*args: Any, **kwargs: Any) -> Any:
            self.tool_calls[name] += 1
            try:
                return fn(*args, **kwargs)
            except Exception:
                self.tool_failures[name] += 1
                raise

        return tool

    def as_dict(self) -> dict[str, Any]:
        return {
            "parse_failures": self.parse_failures,
            "syntax_errors": self.syntax_errors,
            "tool_calls": dict(sorted(self.tool_calls.items())),
            "tool_failures": dict(sorted(self.tool_failures.items())),
            "failed_edits": sum(self.tool_failures[n] for n in ("edit", "patch", "write")),
        }


def normalize_usage(usage: dict[str, Any]) -> dict[str, int]:
    """Input (including cached), cache read, cache write, output and reasoning tokens, from any provider's usage."""

    def first(*keys: str, within: dict[str, Any] | None = None) -> int:
        source = usage if within is None else within
        for key in keys:
            value = source.get(key)
            if isinstance(value, (int, float)) and value:
                return int(value)
        return 0

    prompt_details = usage.get("prompt_tokens_details") or {}
    completion_details = usage.get("completion_tokens_details") or {}
    prompt_details = prompt_details if isinstance(prompt_details, dict) else {}
    completion_details = completion_details if isinstance(completion_details, dict) else {}
    cache_read = first("cache_read_input_tokens", "cache_read_tokens") or first(
        "cached_tokens", "cache_read_tokens", within=prompt_details
    )
    cache_write = first("cache_creation_input_tokens", "cache_write_tokens") or first(
        "cache_creation_tokens", "cache_write_tokens", within=prompt_details
    )
    if "prompt_tokens" in usage:
        total_input = first("prompt_tokens")  # OpenAI-style, and DSPy's normalized usage: cached tokens included
    else:
        # Anthropic's own counters: input_tokens is the uncached part, cache reads and writes come separately
        native = "cache_read_input_tokens" in usage or "cache_creation_input_tokens" in usage
        total_input = first("input_tokens") + (cache_read + cache_write if native else 0)
    return {
        "input": total_input,
        "cache_read": cache_read,
        "cache_write": cache_write,
        "output": first("completion_tokens", "output_tokens"),
        "reasoning": first("reasoning_tokens", within=completion_details) or first("reasoning_tokens"),
    }


def call_records(lm: Any, role: str) -> list[dict[str, Any]]:
    """One record per call the LM made: role, model, normalized and raw usage, cost, time."""
    records = []
    for entry in getattr(lm, "history", None) or []:
        usage = entry.get("usage") or {}
        usage = usage if isinstance(usage, dict) else {}
        cost = entry.get("cost")
        records.append(
            {
                "role": role,
                "model": entry.get("response_model") or entry.get("model") or getattr(lm, "model", ""),
                "timestamp": entry.get("timestamp"),
                "usage": normalize_usage(usage),
                "cost_usd": float(cost) if isinstance(cost, (int, float)) else None,
                "raw_usage": usage,
            }
        )
    return records
