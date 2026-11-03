"""The DSPy internals frond relies on, checked at startup (requirement R9, ledger B11).

frond subclasses ``dspy.RLM`` and overrides private methods of its loop, so a DSPy release that renames one or
changes its parameters would not fail loudly: frond would run, and misbehave. pyproject pins DSPy exactly; this check
covers environments that install another version anyway, and names what changed.
"""

from __future__ import annotations

import importlib
import inspect
import re
from typing import Any

CALLABLE = "callable"  # frond calls it, through whatever signature DSPy gives it
PATTERN = "pattern"  # a compiled regular expression frond matches with

# (module, attribute path, what frond assumes: the names of parameters it passes by position or keyword, in order;
# or CALLABLE; or PATTERN)
EXPECTED: tuple[tuple[str, str, tuple[str, ...] | str], ...] = (
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
    ("dspy.predict.rlm", "RLM._build_variables", CALLABLE),
    ("dspy.predict.rlm", "RLM._format_tool_docs", CALLABLE),
    ("dspy.predict.rlm", "RLM._make_llm_tools", CALLABLE),
    ("dspy.predict.rlm", "_LLMCallBudget", CALLABLE),
    ("dspy.predict.rlm", "_strip_code_fences", CALLABLE),
    ("dspy.adapters.base", "_expand_legacy_custom_type_markers_in_chat_message", CALLABLE),
    ("dspy.adapters.chat_adapter", "field_header_pattern", PATTERN),  # recovering replies off the protocol (D46)
    ("dspy.clients.backend_selection", "select_backend", CALLABLE),
    ("dspy.lm15", "CacheConfig", CALLABLE),
)


def problems() -> list[str]:
    found: list[str] = []
    for module_name, path, expected in EXPECTED:
        name = f"{module_name}.{path}"
        try:
            target: Any = importlib.import_module(module_name)
            for part in path.split("."):
                target = getattr(target, part)
        except (ImportError, AttributeError):
            found.append(f"{name} is missing")
            continue
        if expected == PATTERN:
            if not isinstance(target, re.Pattern):
                found.append(f"{name} is not a compiled pattern")
            continue
        if not callable(target):  # F41: present is not enough when frond calls it
            found.append(f"{name} is not callable")
            continue
        if expected == CALLABLE:
            continue
        try:
            params = list(inspect.signature(target).parameters.values())
        except (TypeError, ValueError):  # unchecked is not compatible (Devin, #28)
            found.append(f"{name}: its signature cannot be read, so its parameters cannot be checked")
            continue
        # F42: frond passes these by position or keyword, so a parameter made keyword- or positional-only, or turned
        # into *args, breaks its calls even with the same names
        shape = [(p.name, p.kind) for p in params]
        if shape != [(n, inspect.Parameter.POSITIONAL_OR_KEYWORD) for n in expected]:
            found.append(f"{name}{inspect.signature(target)} (frond expects ({', '.join(expected)}))")
    return found


def check() -> None:
    """Raise a clear error when the installed DSPy lacks what frond overrides or calls. The CLI calls it before
    anything else; ``Agent`` calls it too, so library use is checked as well (F44). It costs a few lookups."""
    found = problems()
    if found:
        import dspy

        raise RuntimeError(
            f"frond needs the DSPy release it was built against (3.4.1); DSPy {dspy.__version__} differs:\n- "
            + "\n- ".join(found)
            + "\nInstall frond's pinned version: uv sync (or pip install 'dspy==3.4.1')."
        )
