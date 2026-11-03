"""Choosing and constructing the language models frond talks to."""

from __future__ import annotations

import functools
import os
import threading
from dataclasses import dataclass
from typing import Any

import dspy
from dspy._vendor.lm15 import sse
from dspy._vendor.lm15.providers import async_base, base
from dspy.lm15 import CacheConfig

from frond.agent.metrics import normalize_usage

# DSPy's stream parser refuses an SSE line over 64 KiB, but one event's line can carry a whole text delta, and at
# frond's 32,000 output tokens that reaches about 130 KB: E0's first Haiku trial ended on a 100,754-byte line (G36).
# The providers look the parser up by name at each call, so the wider limits apply to every model call frond makes.
SSE_LINE_BYTES = 16 * 1024 * 1024
SSE_EVENT_BYTES = 32 * 1024 * 1024
base.parse_sse = functools.partial(sse.parse_sse, max_line_bytes=SSE_LINE_BYTES, max_event_bytes=SSE_EVENT_BYTES)
async_base.aparse_sse = functools.partial(
    sse.aparse_sse, max_line_bytes=SSE_LINE_BYTES, max_event_bytes=SSE_EVENT_BYTES
)

# (environment variable, main model, sub model): the first key present picks the defaults.
PROVIDER_DEFAULTS: tuple[tuple[str, str, str], ...] = (
    ("ANTHROPIC_API_KEY", "anthropic/claude-opus-5-5", "anthropic/claude-haiku-5-5"),  # decision D24
    ("OPENAI_API_KEY", "openai/gpt-5.5", "openai/gpt-5.4-mini"),
    ("GEMINI_API_KEY", "gemini/gemini-3.1-pro-preview", "gemini/gemini-3-flash-preview"),
    ("GOOGLE_API_KEY", "gemini/gemini-3.1-pro-preview", "gemini/gemini-3-flash-preview"),
)
# Providers served by DSPy's native lm15 engine, where provider-side prompt caching is available.
NATIVE_PREFIXES = ("anthropic/", "openai/", "gemini/", "xai/")


# Failures of the model provider, not of the agent: a run that ends on one says nothing about the harness, so research
# exports flag it and the analysis does not score it (ledger G22). A context overflow or an invalid request is the
# harness's own doing and stays an ordinary failure.
PROVIDER_ERRORS: tuple[type[Exception], ...] = (
    dspy.LMAuthError,
    dspy.LMBillingError,
    dspy.LMRateLimitError,
    dspy.LMTimeoutError,
    dspy.LMServerError,
    dspy.LMTransportError,
)


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


# The public endpoint of each native provider. DSPy reads <PREFIX>_BASE_URL or <PREFIX>_API_BASE in the environment
# as a gateway and sends the call through LiteLLM, which cannot carry prompt_cache. Hosted sessions, Claude Code's
# among them, set ANTHROPIC_BASE_URL to the public endpoint itself; that is no gateway (ledger B1).
PUBLIC_ENDPOINTS = {
    "ANTHROPIC": ("https://api.anthropic.com",),
    "OPENAI": ("https://api.openai.com", "https://api.openai.com/v1"),
    "GEMINI": ("https://generativelanguage.googleapis.com",),
    "XAI": ("https://api.x.ai", "https://api.x.ai/v1"),
}
EFFORTS = ("low", "medium", "high", "xhigh", "max")


def clear_public_endpoint_overrides(model: str) -> list[str]:
    """Unset a base-URL variable that names the provider's own public endpoint; return the names unset."""
    prefix = model.split("/", 1)[0].upper()
    public = PUBLIC_ENDPOINTS.get(prefix, ())
    cleared = []
    for name in (f"{prefix}_BASE_URL", f"{prefix}_API_BASE"):
        value = os.environ.get(name)
        if value is not None and value.strip().rstrip("/") in public:
            del os.environ[name]
            cleared.append(name)
    return cleared


def native_route(lm: dspy.LM) -> bool:
    """Whether DSPy will serve ``lm`` with its native engine (prompt caching, effort) rather than LiteLLM."""
    from dspy.clients.backend_selection import select_backend

    try:
        return select_backend(lm).native
    except Exception:  # an engine DSPy cannot plan offline: it will say so at call time
        return False


def route_of(lm: dspy.LM) -> str:
    """How ``lm`` reaches its provider: "native", or why not (set by ``build_lm``)."""
    return str(getattr(lm, "frond_route", "native" if native_route(lm) else "litellm"))


def build_lm(
    model: str,
    *,
    max_tokens: int = 32_000,
    temperature: float | None = None,
    prompt_cache: bool = True,
    effort: str | None = None,
) -> dspy.LM:
    """A DSPy LM for frond.

    ``effort`` becomes ``output_config.effort`` with adaptive thinking on Claude (low to max). Without it the
    model's default applies, which on Claude Opus 5.5 is ``medium``. Sampling parameters stay unset unless given:
    Claude 5.5 models reject them. Where an environment gateway forces LiteLLM, prompt caching is dropped instead
    of failing every call, and ``lm.frond_route`` says why.
    """
    if effort is not None and effort not in EFFORTS:
        raise ValueError(f"effort must be one of {', '.join(EFFORTS)}, not {effort!r}")
    clear_public_endpoint_overrides(model)
    extra: dict[str, Any] = {"reasoning_effort": effort} if effort else {}
    cache = CacheConfig(mode="auto") if prompt_cache and model.startswith(NATIVE_PREFIXES) else None
    lm = dspy.LM(
        model, cache=False, max_tokens=max_tokens, temperature=temperature, num_retries=3, prompt_cache=cache, **extra
    )
    lm.frond_route = "native"  # ty: ignore[unresolved-attribute]
    if cache is not None and not native_route(lm):
        lm = dspy.LM(model, cache=False, max_tokens=max_tokens, temperature=temperature, num_retries=3, **extra)
        lm.frond_route = "litellm: an environment gateway is set, so prompt caching is off"  # ty: ignore[unresolved-attribute]
    return lm


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
    """Tokens and cost over every call the given LMs made (each LM counted once), whatever shape the provider's
    usage takes (metrics.normalize_usage). Input tokens include cached ones."""
    keys = ("input", "cache_read", "cache_write", "output", "reasoning")
    totals: dict[str, float | int] = {"calls": 0, **{f"{key}_tokens": 0 for key in keys}}
    seen: set[int] = set()
    for lm in lms:
        if id(lm) in seen:
            continue
        seen.add(id(lm))
        for entry in getattr(lm, "history", []) or []:
            usage = entry.get("usage") or {}
            counts = normalize_usage(usage if isinstance(usage, dict) else {})
            totals["calls"] += 1
            for key in keys:
                totals[f"{key}_tokens"] += counts[key]
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
