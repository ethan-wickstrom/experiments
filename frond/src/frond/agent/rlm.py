"""frond's specialisation of ``dspy.RLM``.

The recursion, REPL protocol, SUBMIT handling and extract fallback are DSPy's. This subclass adds what an
interactive coding agent needs around each iteration:

* events for the UI (step started, action planned, execution started/finished, sub-query progress),
* cooperative cancellation between and during steps,
* a tool reference with real signatures and full docstrings,
* previews sized per variable (the whole request and workspace; the tail of the conversation), and
* compaction of the in-turn REPL history when it grows past a budget.
"""

from __future__ import annotations

import contextvars
import inspect
import textwrap
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, cast

import dspy
from dspy.predict.rlm import _LLMCallBudget, _strip_code_fences
from dspy.primitives.prediction import Prediction
from dspy.primitives.repl_types import REPLEntry, REPLHistory, REPLVariable
from dspy.utils.exceptions import format_error_for_lm

from frond.agent.tools import display_signature

ERROR_PREFIXES = ("[Error]", "[Type Error]")
NOTE_CODE = "# compacted"


class Hooks:
    """Callbacks from the RLM loop. The base class does nothing; the session subclasses it."""

    def check(self) -> None:
        """Raise TurnCancelled if the user stopped the turn."""

    def step_started(self, step: int, max_steps: int) -> None: ...

    def before_lm(self, step: int | None) -> None:
        """Called right before a streamed LM call (step None: the max-iterations extract call)."""

    def after_lm(self, step: int | None) -> None: ...

    def step_planned(self, step: int, reasoning: str, code: str) -> None: ...

    def exec_started(self, step: int) -> None: ...

    def exec_finished(self, step: int, output: str, error: str | None, duration: float, final: bool) -> None: ...

    def subquery_progress(self, query_id: int, total: int, done: int) -> None: ...

    def history_budget(self) -> int:
        """Characters of REPL history to keep in the prompt before compacting."""
        return 400_000

    def summarize(self, text: str) -> str | None:
        """Summarise compacted steps (None: fall back to mechanical truncation)."""
        return None

    def compacted(self, steps: int, before: int, after: int) -> None: ...


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    head = limit // 3
    return f"{text[:head]}\n… [{len(text) - limit:,} chars elided] …\n{text[-(limit - head) :]}"


class FrondRLM(dspy.RLM):  # ty: ignore[invalid-base]  (RLM is wrapped by @experimental)
    def __init__(
        self,
        signature: type[dspy.Signature],
        *,
        hooks: Hooks | None = None,
        preview_limits: dict[str, int] | None = None,
        tail_preview: frozenset[str] = frozenset(),
        keep_recent: int = 4,
        **kwargs: Any,
    ) -> None:
        self.hooks = hooks or Hooks()
        self.preview_limits = preview_limits or {}
        self.tail_preview = tail_preview
        self.keep_recent = keep_recent
        self._query_ids = 0
        super().__init__(signature, **kwargs)

    # ── prompt construction ──────────────────────────────────────────────────

    def _format_tool_docs(self, tools: dict[str, Any]) -> str:
        if not tools:
            return ""
        lines = ["", "Tools (global functions in the REPL; everything they do is shown to the user):"]
        for tool in tools.values():
            lines.append(f"- {tool.name}{display_signature(tool.func)}")
            doc = inspect.cleandoc(tool.desc or "")
            if doc:
                lines.append(textwrap.indent(doc, "    "))
        return "\n".join(lines)

    def _build_variables(self, **input_args: Any) -> list[REPLVariable]:
        variables = []
        for name, value in input_args.items():
            field_info = self.signature.input_fields.get(name)
            limit = self.preview_limits.get(name, 1000)
            var = REPLVariable.from_value(name, value, field_info=field_info, preview_chars=limit)
            if name in self.tail_preview and isinstance(value, str) and len(value) > limit:
                preview = f"… (earlier text omitted; print({name}) for all of it)\n" + value[-limit:]
                var = var.model_copy(update={"preview": preview})
            variables.append(var)
        return variables

    # ── sub-LLM tools with progress events ───────────────────────────────────

    def _make_llm_tools(self, budget: _LLMCallBudget | None = None, max_workers: int = 8) -> dict[str, Callable]:
        budget = budget if budget is not None else _LLMCallBudget(self.max_llm_calls)
        sub_lm = self.sub_lm
        hooks = self.hooks

        def query(prompt: str) -> str:
            target = sub_lm if sub_lm is not None else dspy.settings.lm
            if target is None:
                raise dspy.LMNotConfiguredError("No LM configured for llm_query")
            with dspy.context(send_stream=None):
                response = target(prompt)
            if isinstance(response, dspy.lm15.Response):
                return response.text or ""
            if isinstance(response, list) and response:
                first = response[0]
                text = first.get("text") if isinstance(first, dict) else first
                return text if isinstance(text, str) else str(text)
            raise TypeError(f"sub-LM returned {type(response).__name__}")

        def llm_query(prompt: str) -> str:
            """Ask a sub-LLM one question (it sees only this prompt). Good for semantic analysis of text."""
            if not prompt:
                raise ValueError("prompt cannot be empty")
            budget.reserve(1)
            qid = self._next_query_id()
            hooks.subquery_progress(qid, 1, 0)
            try:
                return query(prompt)
            finally:
                hooks.subquery_progress(qid, 1, 1)

        def llm_query_batched(prompts: list[str]) -> list[str]:
            """Ask many independent questions concurrently; returns answers in order ("[ERROR] ..." on failure)."""
            if not prompts:
                return []
            budget.reserve(len(prompts))
            qid = self._next_query_id()
            total, done = len(prompts), 0
            hooks.subquery_progress(qid, total, 0)
            results: dict[int, str] = {}
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {pool.submit(contextvars.copy_context().run, query, p): i for i, p in enumerate(prompts)}
                for future in as_completed(futures):
                    i = futures[future]
                    try:
                        results[i] = cast(str, future.result())
                    except dspy.LMError as exc:
                        results[i] = f"[ERROR] {format_error_for_lm(exc)}"
                    done += 1
                    hooks.subquery_progress(qid, total, done)
            return [results[i] for i in range(total)]

        return {"llm_query": llm_query, "llm_query_batched": llm_query_batched}

    def _next_query_id(self) -> int:
        self._query_ids += 1
        return self._query_ids

    # ── the loop ─────────────────────────────────────────────────────────────

    def _execute_iteration(
        self,
        repl: Any,
        variables: list[REPLVariable],
        history: REPLHistory,
        iteration: int,
        input_args: dict[str, Any],
        output_field_names: list[str],
        interpreter_factory: Any,
        sub_agent_rules: str,
    ) -> Prediction | REPLHistory:
        hooks = self.hooks
        hooks.check()
        history = self._compact(history)
        step = iteration + 1
        hooks.step_started(step, self.max_iters)
        hooks.before_lm(step)
        action = self.generate_action(
            signature=self._action_signature_for_current_factory(interpreter_factory, sub_agent_rules),
            variables_info=[v.format() for v in variables],
            repl_history=history,
            iteration=f"{step}/{self.max_iters}",
        )
        hooks.after_lm(step)
        reasoning = str(action.reasoning or "")
        try:
            code = _strip_code_fences(str(action.code or ""))
        except SyntaxError as exc:
            code = str(action.code or "")
            hooks.step_planned(step, reasoning, code)
            error = f"[Error] {format_error_for_lm(exc)}"
            hooks.exec_finished(step, error, error, 0.0, False)
            return self._process_execution_result(action, code, error, history, output_field_names)
        hooks.step_planned(step, reasoning, code)
        hooks.check()
        hooks.exec_started(step)
        started = time.monotonic()
        result = self._execute_code(repl, code, input_args)
        duration = time.monotonic() - started
        outcome = self._process_execution_result(action, code, result, history, output_field_names)
        if isinstance(outcome, Prediction):
            hooks.exec_finished(step, "", None, duration, True)
        else:
            output = outcome.entries[-1].output
            hooks.exec_finished(step, output, output if output.startswith(ERROR_PREFIXES) else None, duration, False)
        return outcome

    def _extract_fallback(
        self, variables: list[REPLVariable], history: REPLHistory, output_field_names: list[str]
    ) -> Prediction:
        self.hooks.check()
        self.hooks.before_lm(None)
        prediction = super()._extract_fallback(variables, self._compact(history), output_field_names)
        self.hooks.after_lm(None)
        return prediction

    def _compact(self, history: REPLHistory) -> REPLHistory:
        budget = self.hooks.history_budget()
        before = len(history.format())
        if before <= budget or len(history.entries) <= self.keep_recent:
            return history
        entries = list(history.entries)
        old, recent = entries[: -self.keep_recent], entries[-self.keep_recent :]
        # Summaries from earlier compactions are kept whole: clipping them would silently drop what they carry.
        shrunk = [
            e
            if e.code == NOTE_CODE
            else REPLEntry(reasoning=_clip(e.reasoning, 600), code=_clip(e.code, 1500), output=_clip(e.output, 800))
            for e in old
        ]
        compacted = REPLHistory(entries=shrunk + recent, max_output_chars=history.max_output_chars)
        if len(compacted.format()) > budget:
            earlier = [e.output for e in old if e.code == NOTE_CODE]
            steps = [(i, e) for i, e in enumerate(old) if e.code != NOTE_CODE]
            transcript = "\n".join(
                ["Summary of even earlier steps:\n" + text for text in earlier]
                + [e.format(index=i, max_output_chars=4000) for i, e in steps]
            )
            summary = self.hooks.summarize(transcript)
            if summary is None:
                summary = "\n".join(
                    [*earlier]
                    + [f"- step {i + 1}: {_clip(e.reasoning, 200)} → {_clip(e.output.strip(), 200)}" for i, e in steps]
                )
            note = REPLEntry(
                reasoning=f"(steps 1-{len(old)} were compacted to save context)",
                code=NOTE_CODE,
                output="Summary of the earlier steps of this turn:\n" + summary,
            )
            compacted = REPLHistory(entries=[note, *recent], max_output_chars=history.max_output_chars)
        self.hooks.compacted(len(old), before, len(compacted.format()))
        return compacted
