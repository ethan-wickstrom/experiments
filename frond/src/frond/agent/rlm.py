"""frond's specialisation of ``dspy.RLM``.

The recursion, REPL protocol, SUBMIT handling and extract fallback are DSPy's. This subclass adds what an
interactive coding agent needs around each iteration:

* events for the UI (step started, action planned, execution started/finished, sub-query progress),
* cooperative cancellation between and during steps,
* a tool reference with real signatures and full docstrings,
* previews sized per variable (the whole request and workspace; the tail of the conversation),
* a line per name the code has defined, shown with each step (the namespace outlives steps and turns),
* a record of every step in the conversation's step log, and
* folding of the in-turn history when it grows past a budget: early steps become one index line each, and
  nothing is lost, because the step log keeps them whole for ``history_step`` and ``history_search``.
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

from frond.agent.adapter import NOTE_CODE, STEER_CODE, FoldEntry, UserEntry, escape_marker, user_tag
from frond.agent.tools import display_signature

ERROR_PREFIXES = ("[Error]", "[Type Error]")
INDEX_MARK = "Index of the folded steps (oldest first):"
FOLD_GUIDE = (
    "Earlier steps of this turn were folded to keep the prompt within budget. Nothing was lost: "
    "history_step(seq) returns any step's reasoning, code and full output exactly as they were, and "
    "history_search('words') finds anything said, written or printed earlier, in this turn or before."
)
REPL_VARIABLES_DESC = (
    "Names your code has defined in the REPL so far, with their types and sizes. They persist across steps "
    "and turns, so reuse them instead of recomputing."
)
STALE_READS_DESC = (
    "Files you read this turn that changed afterwards, through your own commands or someone else's. What you saw "
    "of them is out of date: read them again before editing them or relying on them."
)


class LoggedEntry(REPLEntry):
    """A history entry that knows where the step log keeps it whole."""

    seq: int | None = None
    step: int = 0


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
        """Characters of REPL history to keep in the prompt before folding early steps into an index."""
        return 400_000

    def record_step(self, step: int, reasoning: str, code: str, output: str, error: bool) -> int | None:
        """Keep a step in the step log; returns its sequence number (None: no log)."""
        return None

    def stale_reads(self, step: int) -> str:
        """Files the model read this turn that changed since (freshness, H3); "(none)" when all still hold."""
        return "(none)"

    def take_messages(self, step: int) -> list[str]:
        """Messages the user sent while the turn ran, to show the model before ``step`` (and forget)."""
        return []

    def preview(self, name: str, value: Any) -> str | None:
        """A custom preview for input variable ``name`` (None: the default)."""
        return None

    def compacted(self, steps: int, before: int, after: int) -> None: ...

    def code_rejected(self, step: int) -> None:
        """The step's code did not compile."""


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
        marker: str = "",
        freshness: bool = False,
        **kwargs: Any,
    ) -> None:
        self.hooks = hooks or Hooks()
        self.freshness = freshness  # show the model which of its reads went stale (H3; hooks.stale_reads)
        self.preview_limits = preview_limits or {}
        self.tail_preview = tail_preview
        self.keep_recent = keep_recent
        # Marks the user's messages in the prompt (see adapter.user_tag); escaped out of everything else frond
        # puts there: previews, the names digest and folded steps. The adapter escapes step outputs.
        self.marker = marker
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
            custom = self.hooks.preview(name, value)  # frond's own previews tag the user's words themselves
            if custom is not None:
                var = var.model_copy(update={"preview": custom})
            elif name in self.tail_preview and isinstance(value, str) and len(value) > limit:
                preview = f"… (earlier text omitted; print({name}) for all of it)\n" + value[-limit:]
                var = var.model_copy(update={"preview": escape_marker(preview, self.marker)})
            else:
                var = var.model_copy(update={"preview": escape_marker(var.preview, self.marker)})
            variables.append(var)
        return variables

    def _action_signature_for_current_factory(self, factory: Any, sub_agent_rules: str) -> type[dspy.Signature]:
        signature = super()._action_signature_for_current_factory(factory, sub_agent_rules)
        if "repl_variables" not in signature.input_fields:
            signature = signature.append("repl_variables", dspy.InputField(desc=REPL_VARIABLES_DESC), type_=str)
        if self.freshness and "stale_reads" not in signature.input_fields:
            signature = signature.append("stale_reads", dspy.InputField(desc=STALE_READS_DESC), type_=str)
        return signature

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
        step = iteration + 1
        steers = hooks.take_messages(step)
        if steers:  # appended, so the cached prefix of the prompt survives
            entries = [UserEntry(reasoning="", code=STEER_CODE, output=text) for text in steers]
            history = REPLHistory(entries=[*history.entries, *entries], max_output_chars=history.max_output_chars)
        history = self._fold(history)
        hooks.step_started(step, self.max_iters)
        hooks.before_lm(step)
        names = getattr(repl, "names", None)
        volatile = {"stale_reads": escape_marker(hooks.stale_reads(step), self.marker)} if self.freshness else {}
        action = self.generate_action(
            signature=self._action_signature_for_current_factory(interpreter_factory, sub_agent_rules),
            variables_info=[v.format() for v in variables],
            repl_history=history,
            iteration=f"{step}/{self.max_iters}",
            repl_variables=escape_marker("\n".join(names), self.marker) if names else "(none yet)",
            **volatile,
        )
        hooks.after_lm(step)
        reasoning = str(action.reasoning or "")
        try:
            code = _strip_code_fences(str(action.code or ""))
        except SyntaxError as exc:
            code = str(action.code or "")
            hooks.step_planned(step, reasoning, code)
            error = f"[Error] {format_error_for_lm(exc)}"
            hooks.code_rejected(step)
            hooks.exec_finished(step, error, error, 0.0, False)
            outcome = self._process_execution_result(action, code, error, history, output_field_names)
            return self._logged(outcome, step, reasoning, code)
        hooks.step_planned(step, reasoning, code)
        hooks.check()
        hooks.exec_started(step)
        started = time.monotonic()
        result = self._execute_code(repl, code, input_args)
        duration = time.monotonic() - started
        if _did_not_compile(result):
            hooks.code_rejected(step)  # protocol adherence (ledger B2)
        outcome = self._process_execution_result(action, code, result, history, output_field_names)
        if isinstance(outcome, Prediction):
            hooks.exec_finished(step, "", None, duration, True)
        else:
            output = outcome.entries[-1].output
            hooks.exec_finished(step, output, output if output.startswith(ERROR_PREFIXES) else None, duration, False)
        return self._logged(outcome, step, reasoning, code)

    def _logged(self, outcome: Prediction | REPLHistory, step: int, reasoning: str, code: str) -> Any:
        """Record the step in the step log, and tag its history entry with the record's sequence number."""
        if isinstance(outcome, Prediction):
            self.hooks.record_step(step, reasoning, code, "(the turn ended here: SUBMIT)", False)
            return outcome
        last = outcome.entries[-1]
        seq = self.hooks.record_step(step, reasoning, code, last.output, last.output.startswith(ERROR_PREFIXES))
        entry = LoggedEntry(reasoning=last.reasoning, code=last.code, output=last.output, seq=seq, step=step)
        return REPLHistory(entries=[*outcome.entries[:-1], entry], max_output_chars=outcome.max_output_chars)

    def _extract_fallback(
        self, variables: list[REPLVariable], history: REPLHistory, output_field_names: list[str]
    ) -> Prediction:
        self.hooks.check()
        self.hooks.before_lm(None)
        prediction = super()._extract_fallback(variables, self._fold(history), output_field_names)
        self.hooks.after_lm(None)
        return prediction

    def _fold(self, history: REPLHistory) -> REPLHistory:
        """Past the budget, replace all but the latest steps with one index line each (seq, headline, outcome).

        Folding instead of summarising keeps the prompt honest: the index says only what each step was and points
        at the full record, and nothing the model has not seen is presented as fact. Steps are folded in bulk,
        so the prompt's cached prefix is invalidated rarely.
        """
        budget = self.hooks.history_budget()
        before = len(history.format())
        if before <= budget or len(history.entries) <= self.keep_recent:
            return history
        old, recent = list(history.entries[: -self.keep_recent]), list(history.entries[-self.keep_recent :])
        tag = user_tag(self.marker)
        who = f"the user {tag}" if tag else "the user"
        lines: list[str] = []
        for entry in old:
            if isinstance(entry, FoldEntry):  # an earlier fold: its lines are already escaped and tagged
                lines.extend(entry.output.split(INDEX_MARK, 1)[-1].strip().splitlines())
            elif isinstance(entry, UserEntry):  # the user's own words are never shortened
                lines.append(f"- {who} wrote, during the turn: " + entry.output.replace("\n", "\n  "))
            else:  # from the step's output, which can say anything: it cannot carry the user's mark
                lines.append(escape_marker(_index_line(entry), self.marker))
        note = FoldEntry(
            reasoning=f"({len(lines)} earlier steps of this turn are folded into an index)",
            code=NOTE_CODE,
            output=f"{FOLD_GUIDE}\n{INDEX_MARK}\n" + "\n".join(lines),
        )
        folded = REPLHistory(entries=[note, *recent], max_output_chars=history.max_output_chars)
        self.hooks.compacted(len(old), before, len(folded.format()))
        return folded


def _did_not_compile(result: Any) -> bool:
    """A step result reporting that the code itself failed to compile, as opposed to failing while it ran."""
    if not isinstance(result, str) or not result.startswith(ERROR_PREFIXES):
        return False
    lines = result.strip().splitlines()
    return '"<repl>"' in lines[0] and lines[-1].startswith(("SyntaxError:", "IndentationError:", "TabError:"))


def _first_line(text: str, limit: int) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("Output ("):
            return line if len(line) <= limit else line[: limit - 1] + "…"
    return "(no output)"


def _index_line(entry: REPLEntry) -> str:
    seq = getattr(entry, "seq", None)
    step = getattr(entry, "step", 0)
    where = f"seq {seq}" if seq is not None else "not in the step log"
    outcome = _first_line(entry.output, 100)
    failed = " [failed]" if entry.output.startswith(ERROR_PREFIXES) else ""
    return f"- step {step or '?'} · {where} · {_first_line(entry.reasoning, 120)} → {outcome}{failed}"
