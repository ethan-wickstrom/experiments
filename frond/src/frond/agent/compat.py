"""The DSPy internals frond relies on, checked at startup (requirement R9, ledger B11).

frond subclasses ``dspy.RLM`` and overrides private methods of its loop, so a DSPy release that renames one or
changes its parameters would not fail loudly: frond would run, and misbehave. pyproject pins DSPy exactly; this check
covers environments that install another version anyway, and names what changed.
"""

from __future__ import annotations

import importlib
import inspect
from typing import Any

# (module, attribute path, the parameter names frond's code assumes; None: it only has to exist)
EXPECTED: tuple[tuple[str, str, tuple[str, ...] | None], ...] = (
    (
        "dspy.predict.rlm",
        "RLM._execute_iteration",
        (
            "self",
            "repl",
            "variables",
            "history",
            "iteration",
            "input_args",
            "output_field_names",
            "interpreter_factory",
            "sub_agent_rules",
        ),
    ),
    (
        "dspy.predict.rlm",
        "RLM._process_execution_result",
        ("self", "pred", "code", "result", "history", "output_field_names"),
    ),
    ("dspy.predict.rlm", "RLM._execute_code", ("self", "repl", "code", "input_args")),
    ("dspy.predict.rlm", "RLM._extract_fallback", ("self", "variables", "history", "output_field_names")),
    ("dspy.predict.rlm", "RLM._action_signature_for_current_factory", ("self", "factory", "sub_agent_rules")),
    ("dspy.predict.rlm", "RLM._build_variables", None),
    ("dspy.predict.rlm", "RLM._format_tool_docs", None),
    ("dspy.predict.rlm", "RLM._make_llm_tools", None),
    ("dspy.predict.rlm", "_LLMCallBudget", None),
    ("dspy.predict.rlm", "_strip_code_fences", None),
    ("dspy.adapters.base", "_expand_legacy_custom_type_markers_in_chat_message", None),
    ("dspy.adapters.chat_adapter", "field_header_pattern", None),  # recovering replies off the protocol (D46)
    ("dspy.clients.backend_selection", "select_backend", None),
    ("dspy.lm15", "CacheConfig", None),
)


def problems() -> list[str]:
    found: list[str] = []
    for module_name, path, params in EXPECTED:
        try:
            target: Any = importlib.import_module(module_name)
            for part in path.split("."):
                target = getattr(target, part)
        except (ImportError, AttributeError):
            found.append(f"{module_name}.{path} is missing")
            continue
        if params is not None:
            try:
                actual = tuple(inspect.signature(target).parameters)
            except (TypeError, ValueError):
                continue
            if actual != params:
                expects = ", ".join(params)
                found.append(f"{module_name}.{path}{inspect.signature(target)} (frond expects {expects})")
    return found


def check() -> None:
    """Raise a clear error when the installed DSPy lacks what frond overrides or calls."""
    found = problems()
    if found:
        import dspy

        raise RuntimeError(
            f"frond needs the DSPy release it was built against (3.4.1); DSPy {dspy.__version__} differs:\n- "
            + "\n- ".join(found)
            + "\nInstall frond's pinned version: uv sync (or pip install 'dspy==3.4.1')."
        )
