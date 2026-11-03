"""What a run did, counted for research (ledger B2, research.md "Measurements per run").

Every model call keeps its provider-reported usage, raw as well as normalized, because cache accounting differs by
provider and the analysis may need fields nobody thought to extract. The counters cover how well the model follows
frond's protocol (replies that do not parse, code that does not compile) and how its tool calls fare. Failed edits are
the H3 and A6 signal.
"""

from __future__ import annotations

import functools
import threading
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunMetrics:
    parse_failures: int = 0  # replies that did not follow the field protocol (protocol adherence, B2)
    parse_recovered: int = 0  # of those, replies whose action was recovered unambiguously (G34)
    unparsed_steps: int = 0  # replies that could not be recovered: the step showed the model an error (G34)
    cut_off_replies: int = 0  # of those, replies that had reached the output limit (G38)
    # the same three for sub-agents' replies, which come from the sub-model and so are kept apart (F51)
    sub_parse_failures: int = 0
    sub_parse_recovered: int = 0
    sub_unparsed_steps: int = 0
    sub_cut_off_replies: int = 0
    syntax_errors: int = 0  # code that did not compile
    stale_actions: int = 0  # edits, writes and deletes of files changed since the model read them (H3, B5)
    compactions: int = 0  # times early steps were folded or summarised to fit the budget (H4, A5)
    summaries: int = 0  # LLM summary calls made by the summary context policy (H4)
    provider_errors: int = 0  # provider failures in sub-agents and llm_query, which the turn survived (F47)
    refusal: str = ""  # the category of the provider refusal that ended the turn, if one did (G43)
    tool_calls: Counter[str] = field(default_factory=Counter)
    tool_failures: Counter[str] = field(default_factory=Counter)  # calls that raised: the model got an error back
    forks: list[list[dict[str, Any]]] = field(default_factory=list)  # each FORK's branches: outcome, steps (H2)
    branch_calls: dict[int, str] = field(default_factory=dict)  # main-LM call index -> the branch that made it
    sub_branch_calls: dict[int, str] = field(default_factory=dict)  # the same for the sub-model's calls (F30)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def bump(self, counter: str, by: int = 1) -> None:
        """Add to a counter. Sub-agents run in threads, and ``+=`` on a shared attribute can lose an update."""
        with self._lock:
            setattr(self, counter, getattr(self, counter) + by)

    def counted(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        """``fn`` as a REPL tool that counts its calls and failures (signature and docs kept for the model)."""
        name = getattr(fn, "__name__", "tool")

        @functools.wraps(fn)
        def tool(*args: Any, **kwargs: Any) -> Any:
            with self._lock:
                self.tool_calls[name] += 1
            try:
                return fn(*args, **kwargs)
            except Exception:
                with self._lock:
                    self.tool_failures[name] += 1
                raise

        return tool

    def as_dict(self) -> dict[str, Any]:
        return {
            "parse_failures": self.parse_failures,
            "parse_recovered": self.parse_recovered,
            "unparsed_steps": self.unparsed_steps,
            "cut_off_replies": self.cut_off_replies,
            "sub_parse_failures": self.sub_parse_failures,
            "sub_parse_recovered": self.sub_parse_recovered,
            "sub_unparsed_steps": self.sub_unparsed_steps,
            "sub_cut_off_replies": self.sub_cut_off_replies,
            "syntax_errors": self.syntax_errors,
            "stale_actions": self.stale_actions,
            "compactions": self.compactions,
            "summaries": self.summaries,
            "provider_errors": self.provider_errors,
            "refusal": self.refusal,
            "tool_calls": dict(sorted(self.tool_calls.items())),
            "tool_failures": dict(sorted(self.tool_failures.items())),
            "failed_edits": sum(self.tool_failures[n] for n in ("edit", "patch", "write")),
            "forks": self.forks,
            "branch_steps": sum(int(b.get("steps") or 0) for fork in self.forks for b in fork),  # in the counters too
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


def call_records(lm: Any, role: str, branches: dict[int, str] | None = None) -> list[dict[str, Any]]:
    """One record per call the LM made: role, model, normalized and raw usage, cost, time. ``branches`` maps call
    indexes to the FORK branch that made them, whose role becomes that branch's scope."""
    records = []
    for index, entry in enumerate(getattr(lm, "history", None) or []):
        usage = entry.get("usage") or {}
        usage = usage if isinstance(usage, dict) else {}
        cost = entry.get("cost")
        records.append(
            {
                "role": (branches or {}).get(index, role),
                "model": entry.get("response_model") or entry.get("model") or getattr(lm, "model", ""),
                "timestamp": entry.get("timestamp"),
                "usage": normalize_usage(usage),
                "cost_usd": float(cost) if isinstance(cost, (int, float)) else None,
                "raw_usage": usage,
            }
        )
    return records
