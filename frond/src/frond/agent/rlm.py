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
import __future__

import ast
import contextvars
import copy
import inspect
import json
import textwrap
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, cast

import dspy
from dspy.predict.rlm import _LLMCallBudget, _strip_code_fences
from dspy.primitives.code_interpreter import FinalOutput
from dspy.primitives.prediction import Prediction
from dspy.primitives.repl_types import REPLEntry, REPLHistory, REPLVariable
from dspy.signatures.signature import make_signature
from dspy.utils.exceptions import AdapterParseError, format_error_for_lm

from frond.agent.adapter import (
    NOTE_CODE,
    STEER_CODE,
    FoldEntry,
    UserEntry,
    escape_marker,
    user_tag,
    without_markers,
)
from frond.agent.control import TurnCancelled
from frond.agent.lm import PROVIDER_ERRORS
from frond.agent.prompts import FORK_GUIDE, SCOPES_GUIDE, TOOL_AGENT_INSTRUCTIONS
from frond.agent.repl import WORKER, ForkRequest
from frond.agent.scopes import ScopeOp
from frond.agent.tools import display_signature

ERROR_PREFIXES = ("[Error]", "[Type Error]")
INDEX_MARK = "Index of the folded steps (oldest first):"
SUMMARY_HEAD = "Summary of the earlier steps of this turn:\n"  # opens the note the summary policy leaves
FOLD_GUIDE = (
    "Earlier steps of this turn were folded to keep the prompt within budget. Nothing was lost: "
    "history_step(seq) returns any step's reasoning, code and full output exactly as they were, and "
    "history_search('words') finds anything said, written or printed earlier, in this turn or before."
)
REPL_VARIABLES_DESC = (
    "Names your code has defined in the REPL so far, with their types and sizes. They persist across steps "
    "and turns, so reuse them instead of recomputing."
)
OPEN_SCOPES_DESC = "The scopes you have opened and not yet closed or abandoned, outermost first."
STALE_READS_DESC = (
    "Files you read this turn that changed afterwards, through your own commands or someone else's. What you saw "
    "of them is out of date: read them again before editing them or relying on them."
)


class LoggedEntry(REPLEntry):
    """A history entry that knows where the step log keeps it whole."""

    seq: int | None = None
    step: int = 0


def _repl_renderers() -> dict[str, Any]:
    """The REPL worker's result classes (commands, jobs, grep matches) and its ``rehydrate``, compiled from
    ``_worker.py`` without running that module, which takes over stdout when imported. The worker runs isolated
    (``python -I``) and cannot import a shared module, so its source stays the one definition of how results print."""
    tree = ast.parse(WORKER.read_text(encoding="utf-8"))
    wanted = {"AttrDict", "CommandResult", "JobHandle", "Matches", "rehydrate"}
    body: list[ast.stmt] = [n for n in tree.body if isinstance(n, ast.ClassDef | ast.FunctionDef) and n.name in wanted]
    namespace: dict[str, Any] = {"Any": Any}
    code = compile(
        ast.Module(body=body, type_ignores=[]), str(WORKER), "exec", flags=__future__.annotations.compiler_flag
    )
    exec(code, namespace)
    return namespace


REHYDRATE = _repl_renderers()["rehydrate"]


def _render_tool_result(value: Any) -> str:
    """A tool's result as the tools arm shows it: what printing it in the REPL would show. Commands, background jobs
    (with the id job_output and job_kill take, F33) and grep matches (grouped by file, F36) print as the REPL prints
    them; other values as JSON."""
    if isinstance(value, str):
        return value or "(empty)"
    if value is None:
        return "(done)"
    if isinstance(value, dict) and value.get("__frond__") in ("command", "job", "matches"):
        return str(REHYDRATE(value))
    return json.dumps(value, indent=1, ensure_ascii=False, default=str)


@dataclass
class Branching:
    """What a FORK step's branches continue from (ledger B7). Each branch replays nothing: it continues the step's
    history, with its own note as the FORK step's output, so every branch's prompt shares the main prompt's prefix
    through the FORK step, which the provider's cache serves."""

    rlm: FrondRLM
    repl: Any
    variables: list[REPLVariable]
    history: REPLHistory
    iteration: int
    input_args: dict[str, Any]
    output_field_names: list[str]
    interpreter_factory: Any
    sub_agent_rules: str
    reasoning: str
    code: str

    def run(self, repl: Any, note: str, steps: int, hooks: Hooks) -> Prediction | REPLHistory:
        """Run one branch in ``repl`` (a fork of the main REPL) for at most ``steps`` steps: its Prediction if it
        called SUBMIT, else its history when the steps ran out."""
        rlm = copy.copy(self.rlm)
        rlm.hooks = hooks
        fork_step = self.iteration + 1
        entry = LoggedEntry(reasoning=self.reasoning, code=self.code, output=note, step=fork_step)
        history = REPLHistory(entries=[*self.history.entries, entry], max_output_chars=self.history.max_output_chars)
        for i in range(steps):
            result = rlm._execute_iteration(
                repl, self.variables, history, fork_step + i, self.input_args, self.output_field_names,
                self.interpreter_factory, self.sub_agent_rules,
            )  # fmt: skip
            if isinstance(result, Prediction):
                return result
            history = result
        return history


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

    def fork(self, step: int, request: ForkRequest, branching: Branching) -> str:
        """Explore the options of a FORK and return the step's output (ledger B7)."""
        return "FORK is not available here."

    def take_messages(self, step: int) -> list[str]:
        """Messages the user sent while the turn ran, to show the model before ``step`` (and forget)."""
        return []

    def preview(self, name: str, value: Any) -> str | None:
        """A custom preview for input variable ``name`` (None: the default)."""
        return None

    def folded(self, steps: int, before: int, after: int) -> None: ...

    def scope_ops(self) -> list[ScopeOp]:
        """Scopes closed or abandoned during the last step, to apply to the history now (H5, ledger B9)."""
        return []

    def open_scopes(self) -> str:
        """The prompt field listing the open scopes."""
        return "(none)"

    def summarize(self, transcript: str) -> str | None:
        """An LLM summary of earlier steps, for the summary context policy (H4); None when it cannot be made."""
        return None

    def code_rejected(self, step: int) -> None:
        """The step's code did not compile."""

    def provider_error(self) -> None:
        """A model call inside an llm_query or a sub-agent failed for the provider's reasons (F47)."""

    def reply_unparsed(self, step: int, cut_off: bool) -> None:
        """The step's reply followed no format frond can read, so the model was shown an error (G34); ``cut_off``:
        the reply had reached the output limit (G38)."""


def _cut_off(completion: str) -> bool:
    """Whether the call that returned ``completion`` stopped at the output limit. The LM's history is shared with
    sub-agents and FORK branches in other threads, so the call is found by its output, not taken as the latest."""
    history = getattr(dspy.settings.lm, "history", None) or []
    for entry in reversed(history[-50:]):
        outputs = entry.get("outputs") or []
        texts = [o if isinstance(o, str) else (o.get("text") if isinstance(o, dict) else None) for o in outputs]
        if completion in texts:
            return getattr(entry.get("response"), "finish_reason", None) == "length"
    return False


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
        max_branches: int = 1,
        action_space: str = "code",
        context: str = "fold",
        scopes: bool = False,
        **kwargs: Any,
    ) -> None:
        self.scopes = scopes  # scopes as savepoints: the tools, the open_scopes field and the guide (H5, B9)
        if context not in ("fold", "summary"):
            raise ValueError(f"context must be 'fold' or 'summary', not {context!r}")
        self.context = context  # past the budget: fold early steps into an index, or summarise them (H4, B10)
        if action_space not in ("code", "tools"):
            raise ValueError(f"action_space must be 'code' or 'tools', not {action_space!r}")
        self.action_space = action_space  # "code": Python in the REPL; "tools": one tool call per step (H1, B8)
        self._tools_signature: type[dspy.Signature] | None = None
        self.hooks = hooks or Hooks()
        self.freshness = freshness  # show the model which of its reads went stale (H3; hooks.stale_reads)
        self.max_branches = max_branches  # FORK is documented, and defined in the REPL, from 2 (H2, ledger B7)
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

    # ── the tool-calling arm (H1, ledger B8) ─────────────────────────────────

    def _tool_signature(self) -> type[dspy.Signature]:
        """The action signature of the tools arm: the same tools and documentation, one call per step."""
        if self._tools_signature is None:
            docs = ["", "Tools (call one per step; `args` is a JSON object of its parameters):"]
            for tool in self._user_tools.values():
                docs.append(f"- {tool.name}{display_signature(tool.func)}")
                doc = inspect.cleandoc(tool.desc or "")
                if doc:
                    docs.append(textwrap.indent(doc, "    "))
            docs.append("- submit(response: str)\n    End the turn with your reply to the user, in a step of its own.")
            signature = make_signature({}, TOOL_AGENT_INSTRUCTIONS + "\n".join(docs))
            fields: list[tuple[str, Any, Any]] = [
                ("variables_info", dspy.InputField(desc="The request, history, workspace and attachments"), str),
                ("repl_history", dspy.InputField(desc="Your earlier steps: each call and its result"), REPLHistory),
                ("iteration", dspy.InputField(desc="The current step (1-indexed) out of the maximum"), str),
                ("reasoning", dspy.OutputField(desc="What you know, what remains, why this call is next"), str),
                ("tool", dspy.OutputField(desc="The name of one tool, or submit"), str),
                ("args", dspy.OutputField(desc="The tool's arguments, as a JSON object"), dict[str, Any]),
            ]
            for name, field, kind in fields:
                signature = signature.append(name, field, type_=kind)
            self._tools_signature = signature
        signature = self._tools_signature
        if self.freshness:
            signature = signature.append("stale_reads", dspy.InputField(desc=STALE_READS_DESC), type_=str)
        return self._with_scopes(signature)

    def _tool_context(self, input_args: dict[str, Any]) -> list[str]:
        """The inputs as text: without a REPL, the model reads them here, clipped like the REPL's previews."""
        out = []
        for name, value in input_args.items():
            custom = self.hooks.preview(name, value)  # the RLM arm's own previews: every user message kept (F32)
            if custom is not None:
                out.append(f"`{name}`:\n{custom}")
                continue
            text = value if isinstance(value, str) else json.dumps(value, indent=1, ensure_ascii=False, default=str)
            limit = self.preview_limits.get(name, 20_000)
            if len(text) > limit:
                cut = len(text) - limit
                text = (
                    f"[{cut:,} earlier characters not shown]\n{text[-limit:]}"
                    if name in self.tail_preview
                    else f"{text[:limit]}\n[{cut:,} more characters not shown]"
                )
            out.append(f"`{name}`:\n{escape_marker(text, self.marker) if name != 'request' else text}")
        return out

    def _tool_step(
        self,
        step: int,
        history: REPLHistory,
        input_args: dict[str, Any],
        output_field_names: list[str],
        volatile: dict[str, str],
    ) -> Prediction | REPLHistory:
        hooks = self.hooks
        try:
            action = self.generate_action(
                signature=self._tool_signature(),
                variables_info=self._tool_context(input_args),
                repl_history=history,
                iteration=f"{step}/{self.max_iters}",
                **volatile,
            )
        except AdapterParseError as exc:
            hooks.after_lm(step)
            return self._unparsed(step, exc, history, output_field_names)
        hooks.after_lm(step)
        reasoning = str(action.reasoning or "")
        name = str(getattr(action, "tool", "") or "").strip()
        args = getattr(action, "args", None)
        args = args if isinstance(args, dict) else {}
        call = json.dumps({"tool": name, "args": args}, ensure_ascii=False, default=str)
        shown = f"{name}({', '.join(f'{k}={v!r}' for k, v in args.items())})"
        hooks.step_planned(step, reasoning, shown)
        hooks.check()
        hooks.exec_started(step)
        started = time.monotonic()
        result: Any
        if name == "submit" and set(args) != set(output_field_names):  # SUBMIT in the REPL refuses these too (F34)
            wanted = ", ".join(output_field_names)
            result = f"[Error] submit takes exactly these arguments: {wanted}; it got: {', '.join(args) or 'none'}."
        elif name == "submit":
            result = FinalOutput({field: args[field] for field in output_field_names})
        elif (tool := self._user_tools.get(name)) is None:
            known = ", ".join([*sorted(self._user_tools), "submit"])
            result = f"[Error] There is no tool named {name!r}. The tools are: {known}."
        else:
            try:
                result = _render_tool_result(tool(**args))
            except TurnCancelled:
                raise
            except Exception as exc:
                result = f"[Error] {type(exc).__name__}: {exc}"
        outcome = self._process_execution_result(action, call, result, history, output_field_names)
        output = "" if isinstance(outcome, Prediction) else outcome.entries[-1].output
        error = output if output.startswith(ERROR_PREFIXES) else None
        hooks.exec_finished(step, output, error, time.monotonic() - started, isinstance(outcome, Prediction))
        return self._logged(outcome, step, reasoning, call)  # the call as JSON: tool and args, for exports (F35)

    def _action_signature_for_current_factory(self, factory: Any, sub_agent_rules: str) -> type[dspy.Signature]:
        signature = super()._action_signature_for_current_factory(factory, sub_agent_rules)
        if "repl_variables" not in signature.input_fields:
            signature = signature.append("repl_variables", dspy.InputField(desc=REPL_VARIABLES_DESC), type_=str)
        if self.freshness and "stale_reads" not in signature.input_fields:
            signature = signature.append("stale_reads", dspy.InputField(desc=STALE_READS_DESC), type_=str)
        if self.max_branches > 1 and "Branching\n" not in signature.instructions:
            signature = signature.with_instructions(
                signature.instructions + FORK_GUIDE.format(branches=self.max_branches)
            )
        return self._with_scopes(signature)

    def _with_scopes(self, signature: type[dspy.Signature]) -> type[dspy.Signature]:
        if not self.scopes or "open_scopes" in signature.input_fields:
            return signature
        signature = signature.with_instructions(signature.instructions + SCOPES_GUIDE)
        return signature.append("open_scopes", dspy.InputField(desc=OPEN_SCOPES_DESC), type_=str)

    def _apply_scopes(self, history: REPLHistory, ops: list[ScopeOp]) -> REPLHistory:
        """Collapse each closed scope's steps into one entry, and cut an abandoned one's away with a note. The
        steps are the tail of the history, so the prompt prefix before the scope stays as it was; the user's
        messages from inside the scope are kept."""
        for op in ops:
            entries = list(history.entries)
            start = next(
                (i for i, e in enumerate(entries) if isinstance(e, LoggedEntry) and e.step >= op.scope.step),
                len(entries),
            )
            region = entries[start:]
            users = [e for e in region if isinstance(e, UserEntry)]
            seqs = [e.seq for e in region if isinstance(e, LoggedEntry) and e.seq]
            where = f"Its steps are log seq {min(seqs)}-{max(seqs)}" if seqs else "Its steps are in the step log"
            where += "; history_step(seq) shows any of them." if self.context == "fold" else "."
            if op.kind == "close":
                text = f"Scope closed: {op.scope.goal}\nResult: {op.text}\n{where}"
            else:
                text = f"Abandoned: {op.scope.goal}\nWhy: {op.text}\n{op.note}\n{where}"
            note = FoldEntry(
                reasoning=f"({'closed' if op.kind == 'close' else 'abandoned'} scope: {op.scope.goal})",
                code=NOTE_CODE,
                output=escape_marker(text, self.marker),
            )
            history = REPLHistory(entries=[*entries[:start], note, *users], max_output_chars=history.max_output_chars)
        return history

    # ── sub-LLM tools with progress events ───────────────────────────────────

    def _make_llm_tools(self, budget: _LLMCallBudget | None = None, max_workers: int = 8) -> dict[str, Callable]:
        budget = budget if budget is not None else _LLMCallBudget(self.max_llm_calls)
        sub_lm = self.sub_lm
        hooks = self.hooks

        def query(prompt: str) -> str:
            target = sub_lm if sub_lm is not None else dspy.settings.lm
            if target is None:
                raise dspy.LMNotConfiguredError("No LM configured for llm_query")
            try:
                with dspy.context(send_stream=None):
                    response = target(prompt)
            except PROVIDER_ERRORS as exc:
                hooks.provider_error()  # the turn goes on, but a run that saw them is not like one that did not
                exc.frond_counted = True  # ty: ignore[unresolved-attribute] - so a sub-agent does not count it again
                raise
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
        history = self._apply_scopes(history, hooks.scope_ops())
        steers = hooks.take_messages(step)
        if steers:  # appended, so the cached prefix of the prompt survives
            entries = [UserEntry(reasoning="", code=STEER_CODE, output=text) for text in steers]
            history = REPLHistory(entries=[*history.entries, *entries], max_output_chars=history.max_output_chars)
        history = self._fold(history)
        hooks.step_started(step, self.max_iters)
        hooks.before_lm(step)
        volatile = {"stale_reads": escape_marker(hooks.stale_reads(step), self.marker)} if self.freshness else {}
        if self.scopes:
            volatile["open_scopes"] = escape_marker(hooks.open_scopes(), self.marker)
        if self.action_space == "tools":
            return self._tool_step(step, history, input_args, output_field_names, volatile)
        names = getattr(repl, "names", None)
        try:
            action = self.generate_action(
                signature=self._action_signature_for_current_factory(interpreter_factory, sub_agent_rules),
                variables_info=[v.format() for v in variables],
                repl_history=history,
                iteration=f"{step}/{self.max_iters}",
                repl_variables=escape_marker("\n".join(names), self.marker) if names else "(none yet)",
                **volatile,
            )
        except AdapterParseError as exc:
            hooks.after_lm(step)
            return self._unparsed(step, exc, history, output_field_names)
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
        if isinstance(result, ForkRequest):  # the step ended at FORK: the branches' outcome is its output
            branching = Branching(
                self, repl, variables, history, iteration, input_args, output_field_names,
                interpreter_factory, sub_agent_rules, reasoning, code,
            )  # fmt: skip
            result = hooks.fork(step, result, branching)
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

    def _unparsed(
        self, step: int, exc: AdapterParseError, history: REPLHistory, output_field_names: list[str]
    ) -> Prediction | REPLHistory:
        """A step whose reply could not be read: nothing runs, and the model sees its reply and what was expected,
        at the cost of a step, instead of the turn ending (G34). The reply, without field markers, stands as the
        step's reasoning, so the history shows the model its own words in the format it must use."""
        hooks = self.hooks
        completion = str(exc.lm_response or "")
        cut_off = _cut_off(completion)
        hooks.reply_unparsed(step, cut_off)
        reply = _clip(without_markers(completion), 4_000) or "(an empty reply)"
        if self.action_space == "tools":
            fields, empty = "`[[ ## tool ## ]]` with the tool's name, then `[[ ## args ## ]]` with a JSON object", "{}"
        else:
            fields, empty = "`[[ ## code ## ]]` with one ```python block", ""
        why = (  # G38: a reply cut off at the output limit is no format error, and needs a shorter step, not markers
            "Your reply reached the output limit and was cut off before it ended, so nothing ran. Take a smaller "
            "step: write less code or reasoning at once."
            if cut_off
            else "Your reply did not follow the step format, so nothing ran."
        )
        error = (
            f"[Error] {why} Reply with `[[ ## reasoning ## ]]`, then {fields}, then `[[ ## completed ## ]]`, and put "
            "nothing before the first marker."
        )
        hooks.step_planned(step, reply, empty)
        hooks.exec_finished(step, error, error, 0.0, False)
        action = Prediction(reasoning=reply, code=empty)
        outcome = self._process_execution_result(action, empty, error, history, output_field_names)
        return self._logged(outcome, step, reply, empty)

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
        if all(isinstance(e, (FoldEntry, UserEntry)) for e in old):
            return history  # only notes and the user's words are left, which neither policy shortens
        if self.context == "summary":
            return self._summarize(old, recent, history, before)
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
        self.hooks.folded(len(old), before, len(folded.format()))
        return folded

    def _summarize(
        self, old: list[REPLEntry], recent: list[REPLEntry], history: REPLHistory, before: int
    ) -> REPLHistory:
        """H4's control arm, as products compact a long session: the early steps and any earlier summary become one
        LLM-written summary, and nothing points back to the steps. The user's messages among them stay verbatim,
        in order, ahead of the summary, as Codex keeps them and as the fold keeps them, so the two arms differ only
        in how the agent's own steps are compacted (D38). The summary, written from tool output, cannot carry the
        user's mark."""
        users = [e for e in old if isinstance(e, UserEntry)]
        earlier = [e.output.removeprefix(SUMMARY_HEAD) for e in old if isinstance(e, FoldEntry)]
        steps = [e for e in old if not isinstance(e, (FoldEntry, UserEntry))]
        parts = []
        for i, entry in enumerate(old, start=1):
            if isinstance(entry, FoldEntry):
                parts.append("Summary of even earlier steps:\n" + entry.output.removeprefix(SUMMARY_HEAD))
            elif isinstance(entry, UserEntry):
                parts.append(f"The user wrote, during the turn:\n{entry.output}")
            else:
                parts.append(entry.format(index=i, max_output_chars=4000))
        summary = self.hooks.summarize("\n\n".join(parts))
        if not summary:  # the call failed: keep the earlier summaries, and a clipped trace of the steps since them
            summary = "\n\n".join([*earlier, "\n".join(_index_line(e) for e in steps)])
        note = FoldEntry(
            reasoning=f"({len(steps)} earlier steps of this turn were summarised to save context)",
            code=NOTE_CODE,
            output=SUMMARY_HEAD + escape_marker(summary, self.marker),
        )
        summarised = REPLHistory(entries=[*users, note, *recent], max_output_chars=history.max_output_chars)
        self.hooks.folded(len(steps), before, len(summarised.format()))
        return summarised


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
