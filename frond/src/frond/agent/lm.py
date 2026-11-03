"""Choosing and constructing the language models frond talks to."""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass

import dspy
from dspy.lm15 import CacheConfig

# (environment variable, main model, sub model): the first key present picks the defaults.
PROVIDER_DEFAULTS: tuple[tuple[str, str, str], ...] = (
    ("ANTHROPIC_API_KEY", "anthropic/claude-sonnet-5-5", "anthropic/claude-haiku-5-5"),
    ("OPENAI_API_KEY", "openai/gpt-5.5", "openai/gpt-5.4-mini"),
    ("GEMINI_API_KEY", "gemini/gemini-3.1-pro-preview", "gemini/gemini-3-flash-preview"),
    ("GOOGLE_API_KEY", "gemini/gemini-3.1-pro-preview", "gemini/gemini-3-flash-preview"),
)
# Providers served by DSPy's native lm15 engine, where provider-side prompt caching is available.
NATIVE_PREFIXES = ("anthropic/", "openai/", "gemini/", "xai/")


def caches_by_marks(model: str) -> bool:
    """True for providers that cache only up to blocks marked as breakpoints (Anthropic); the others cache any
    repeated prefix on their own."""
    return model.startswith("anthropic/")


DEFAULT_CONTEXT_WINDOW = 200_000


class ModelConfigError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ModelChoice:
    main: str
    sub: str
    source: str


def resolve_models(model: str | None = None, sub_model: str | None = None) -> ModelChoice:
    model = model or os.environ.get("FROND_MODEL")
    sub_model = sub_model or os.environ.get("FROND_SUB_MODEL")
    if model:
        return ModelChoice(model, sub_model or _default_sub(model) or model, "configured")
    for key, main, sub in PROVIDER_DEFAULTS:
        if os.environ.get(key):
            return ModelChoice(main, sub_model or sub, f"${key}")
    raise ModelConfigError(
        "No model configured. Set ANTHROPIC_API_KEY, OPENAI_API_KEY or GEMINI_API_KEY, or pass "
        "--model provider/name (any model string DSPy accepts, e.g. anthropic/claude-sonnet-5-5). "
        "To look around without a key, run: frond --demo"
    )


def _default_sub(model: str) -> str | None:
    for _key, main, sub in PROVIDER_DEFAULTS:
        if model.split("/", 1)[0] == main.split("/", 1)[0]:
            return sub
    return None


def build_lm(
    model: str, *, max_tokens: int = 32_000, temperature: float | None = None, prompt_cache: bool = True
) -> dspy.LM:
    cache = CacheConfig(mode="auto") if prompt_cache and model.startswith(NATIVE_PREFIXES) else None
    return dspy.LM(
        model, cache=False, max_tokens=max_tokens, temperature=temperature, num_retries=3, prompt_cache=cache
    )


_window_cache: dict[str, int | None] = {}
_window_lock = threading.Lock()


def context_window(model: str) -> int | None:
    """The model's input window from DSPy's model metadata, or None if unknown. May block briefly once."""
    with _window_lock:
        if model in _window_cache:
            return _window_cache[model]
    window: int | None = None
    try:
        from dspy.clients.model_metadata import model_info

        provider, _, name = model.partition("/")
        info = model_info(provider, name) if name else model_info("openai", provider)
        if info:
            value = info.get("max_input_tokens") or info.get("max_tokens")
            window = int(value) if value else None
    except Exception:
        window = None
    with _window_lock:
        _window_cache[model] = window
    return window


def last_usage(lm: dspy.LM) -> tuple[int, int, int]:
    """(prompt, completion, cached) tokens of the LM's most recent call."""
    if not getattr(lm, "history", None):
        return 0, 0, 0
    usage = lm.history[-1].get("usage") or {}
    prompt = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
    completion = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    details = usage.get("prompt_tokens_details") or {}
    cached = int(
        (details.get("cached_tokens") if isinstance(details, dict) else 0) or usage.get("cache_read_tokens") or 0
    )
    return prompt, completion, cached


def usage_totals(*lms: dspy.LM) -> dict[str, float | int]:
    """Tokens and cost over every call the given LMs made (each LM counted once)."""
    totals: dict[str, float | int] = {"calls": 0, "input_tokens": 0, "cache_read_tokens": 0, "output_tokens": 0}
    seen: set[int] = set()
    for lm in lms:
        if id(lm) in seen:
            continue
        seen.add(id(lm))
        for entry in getattr(lm, "history", []) or []:
            usage = entry.get("usage") or {}
            details = usage.get("prompt_tokens_details") or {}
            totals["calls"] += 1
            totals["input_tokens"] += int(usage.get("prompt_tokens") or 0)  # includes cached tokens
            totals["cache_read_tokens"] += int((details.get("cached_tokens") if isinstance(details, dict) else 0) or 0)
            totals["output_tokens"] += int(usage.get("completion_tokens") or 0)
    totals["cost_usd"] = round(total_cost(*lms), 6)
    return totals


def total_cost(*lms: dspy.LM) -> float:
    seen: set[int] = set()
    cost = 0.0
    for lm in lms:
        if id(lm) in seen:
            continue
        seen.add(id(lm))
        for entry in getattr(lm, "history", []) or []:
            value = entry.get("cost")
            if isinstance(value, (int, float)):
                cost += float(value)
    return cost
