"""Command-line entry point: ``frond`` (interactive TUI), ``frond -p`` (headless), ``frond --demo``."""

from __future__ import annotations

import argparse
import contextlib
import logging
import os
import sys
import threading
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

from frond import __version__

if TYPE_CHECKING:
    from collections.abc import Callable

    import dspy

    from frond.agent.session import Agent, AgentConfig, TurnRecord
    from frond.workspace import Workspace


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="frond",
        description="An RLM-centric coding agent for the terminal, built on DSPy.",
        epilog="Models are any DSPy model string (provider/name). Defaults follow your API keys: "
        "ANTHROPIC_API_KEY, OPENAI_API_KEY or GEMINI_API_KEY. Set FROND_MODEL / FROND_SUB_MODEL to override.",
    )
    p.add_argument("prompt", nargs="*", help="an initial message (interactive) or the task (with -p)")
    p.add_argument(
        "-p",
        "--print",
        dest="print_mode",
        action="store_true",
        help="run one turn without the TUI: progress on stderr, the answer on stdout",
    )
    p.add_argument("--json", action="store_true", help="with -p: write every event as a JSON line on stdout")
    p.add_argument(
        "-c",
        "--continue",
        dest="resume",
        action="store_true",
        help="continue the most recent conversation in this workspace",
    )
    p.add_argument("-m", "--model", help="main model, e.g. anthropic/claude-opus-5-5")
    p.add_argument("--sub-model", help="model for llm_query sub-calls and sub-agents (default: a smaller sibling)")
    p.add_argument(
        "--effort",
        choices=("low", "medium", "high", "xhigh", "max", "default"),
        default="high",
        help="the main model's reasoning effort (default high; 'default' leaves it to the model)",
    )
    p.add_argument("-C", "--cwd", type=Path, help="workspace directory (default: the current directory)")
    p.add_argument("--max-steps", type=int, default=40, help="REPL steps per turn before wrapping up (default 40)")
    p.add_argument("--step-timeout", type=float, default=600, help="seconds one REPL step may run (default 600)")
    p.add_argument("--context-window", type=int, help="override the model's context window (tokens)")
    approvals = p.add_mutually_exclusive_group()
    approvals.add_argument("--yolo", action="store_true", help="never ask before risky commands or outside writes")
    approvals.add_argument(
        "--read-only", action="store_true", help="forbid file changes; commands run in a read-only OS sandbox"
    )
    p.add_argument("--theme", choices=["auto", "dark", "light"], default="auto")
    p.add_argument("--no-mouse", action="store_true", help="leave the mouse to the terminal (native selection)")
    p.add_argument("--no-prompt-cache", action="store_true", help="disable provider-side prompt caching")
    p.add_argument(
        "--layout",
        choices=["turns", "chat"],
        default="turns",
        help="how each step sees the history: turns (frond's, cache-friendly) or chat (DSPy's stock layout); "
        "an experiment arm (H6)",
    )
    p.add_argument(
        "--freshness",
        choices=["on", "off"],
        default="on",
        help="tell the model which files changed since it read them, and refuse to overwrite them unread; "
        "off only counts such actions (an experiment arm, H3)",
    )
    p.add_argument(
        "--arm",
        choices=["rlm", "react"],
        default="rlm",
        help="rlm: act by writing Python in a persistent REPL (frond); react: one tool call per step with the same "
        "tools, prompt layout and harness (an experiment arm, H1)",
    )
    p.add_argument(
        "--context",
        choices=["fold", "summary"],
        default="fold",
        help="past the context budget: fold early steps into an index the model can search (frond), or replace "
        "them with a summary the main model writes (an experiment arm, H4)",
    )
    p.add_argument(
        "--scopes",
        choices=["on", "off"],
        default="off",
        help="give the model scopes: open a subtask, close it into one entry, or abandon it and rewind the "
        "workspace (default off; an experiment arm, H5)",
    )
    p.add_argument(
        "--fork",
        type=int,
        default=1,
        metavar="K",
        help="let the model FORK up to K branches and keep the one its check passes; 1 turns FORK off "
        "(default 1; an experiment arm, H2)",
    )
    p.add_argument(
        "--demo", action="store_true", help="scripted session in a temporary sample project (no API key needed)"
    )
    p.add_argument(
        "--script",
        type=Path,
        metavar="FILE",
        help="developer playground: replay model steps from a JSON list of {reasoning, code} objects "
        "({reasoning, tool, args} with --arm react)",
    )
    p.add_argument("-v", "--verbose", action="store_true", help="with -p: also print each step's code")
    p.add_argument(
        "--export",
        type=Path,
        metavar="DIR",
        help="with -p: write the run's record to DIR (steps.jsonl, usage.json, answer.md), e.g. for benchmarks",
    )
    p.add_argument("--version", action="version", version=f"frond {__version__}")
    return p.parse_args(argv)


def log_path() -> Path:
    base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "frond"
    base.mkdir(parents=True, exist_ok=True)
    return base / "frond.log"


def configure_logging(to_stderr: bool) -> Path:
    path = log_path()
    handlers: list[logging.Handler] = [logging.FileHandler(path, encoding="utf-8")]
    if to_stderr:
        stream = logging.StreamHandler(sys.stderr)
        stream.setLevel(logging.ERROR)
        handlers.append(stream)
    logging.basicConfig(
        level=logging.WARNING, handlers=handlers, force=True, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    logging.captureWarnings(True)
    warnings.filterwarnings("ignore", category=UserWarning, module=r"dspy\..*")
    return path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    os.environ.setdefault("LITELLM_LOG", "ERROR")
    from frond.tui.terminal import Terminal

    interactive = not args.print_mode and Terminal.available()
    configure_logging(to_stderr=not interactive)

    from frond.agent import compat

    try:
        compat.check()  # an incompatible DSPy fails here, with what changed (R9)
    except RuntimeError as exc:
        print(f"frond: {exc}", file=sys.stderr)
        return 2

    from frond.agent.lm import ModelConfigError, resolve_models
    from frond.agent.scripted import scripted_lm
    from frond.agent.session import Agent, AgentConfig
    from frond.workspace import Workspace

    lm = None
    note = None
    if args.script:
        import json

        from frond.agent.scripted import ScriptedEngine, Step, ToolStep

        spec = json.loads(args.script.read_text())
        entries = spec if isinstance(spec, list) else spec.get("steps", [])
        tools_arm = args.arm == "react"
        if any(("tool" in s) != tools_arm for s in entries):  # a reply the arm cannot parse would replay as errors
            shape = "{reasoning, tool, args}" if tools_arm else "{reasoning, code}"
            print(f"frond: with --arm {args.arm}, every script entry must be {shape}", file=sys.stderr)
            return 2
        steps: list[Step | ToolStep] = [  # {reasoning, tool, args} for the tools arm (F37)
            ToolStep(s["reasoning"], s["tool"], s.get("args", {})) if tools_arm else Step(s["reasoning"], s["code"])
            for s in entries
        ]
        delay = float(spec.get("delay", 0.01)) if isinstance(spec, dict) else 0.01
        lm = scripted_lm(ScriptedEngine(steps, chunk=6, delay=delay if interactive else 0.0))
        model = sub_model = "frond/scripted"
        root = (args.cwd or Path.cwd()).expanduser().resolve()
        note = f"Replaying {len(steps)} scripted steps from {args.script}"
    elif args.demo:
        from frond import demo

        root = demo.make_project()
        lm = scripted_lm(demo.make_engine(delay=0.012 if interactive else 0.0))
        model = sub_model = "frond/scripted-demo"
        note = f"Demo mode: scripted replies in a sample project at {root}. Try: {demo.SUGGESTION}"
    else:
        root = (args.cwd or Path.cwd()).expanduser().resolve()
        if not root.is_dir():
            print(f"frond: {root} is not a directory", file=sys.stderr)
            return 2
        try:
            choice = resolve_models(args.model, args.sub_model)
        except ModelConfigError as exc:
            print(f"frond: {exc}", file=sys.stderr)
            return 2
        model, sub_model = choice.main, choice.sub

    workspace = Workspace(root)
    config = AgentConfig(
        model=model,
        sub_model=sub_model,
        max_steps=args.max_steps,
        step_timeout=args.step_timeout,
        approval="yolo" if args.yolo else "readonly" if args.read_only else "auto",
        context_window=args.context_window or (200_000 if args.demo or args.script else None),
        prompt_cache=not args.no_prompt_cache,
        effort=None if args.effort == "default" else args.effort,
        layout=args.layout,
        freshness=args.freshness == "on",
        fork=max(1, args.fork),
        arm=args.arm,
        context=args.context,
        scopes=args.scopes == "on",
    )
    prompt = " ".join(args.prompt).strip()

    from frond.sessions import SessionStore

    store = SessionStore(workspace.root)
    session_file = store.new_path()
    restored = []
    if args.resume:
        latest = store.latest()
        if latest is None:
            print("frond: no earlier conversation in this workspace; starting a new one", file=sys.stderr)
        else:
            session_file, restored = latest, store.load(latest)

    current = [session_file]  # /new moves the conversation to a new session file

    def persist(records: list) -> None:
        store.save(current[0], records, model)

    def new_log() -> Path:
        current[0] = store.new_path()
        return store.steps_path(current[0])

    world_dir = store.directory / "world"  # shared by the workspace's sessions, so --continue can still /undo
    if world_dir.is_dir():  # past its bound, drop what no recent session reaches (ledger G21), in the background
        from frond.world import Store

        threading.Thread(
            target=store.collect,
            args=(Store(world_dir),),
            kwargs={"keep": session_file},  # a continued session keeps its undo history, however old (F46)
            name="frond-world-gc",
            daemon=True,
        ).start()
    if not interactive:
        return run_headless(
            args, config, workspace, prompt, lm, persist, restored, store.steps_path(session_file), world_dir
        )

    from frond.tui.app import App
    from frond.tui.style import detect_color_mode

    app = App(workspace, model=model, sub_model=sub_model, color_mode=detect_color_mode(), note=note)
    agent = Agent(
        config,
        workspace,
        app.emit,
        approver=app.approver,
        lm=lm,
        sub_lm=lm,
        persist=persist,
        new_log=new_log,
        world_dir=world_dir,
    )
    agent.attach_log(store.steps_path(session_file))
    app.attach(agent)
    if restored:
        agent.restore(restored)
        app.restore(restored, session_file.name)
    if prompt:
        app.start_turn(prompt)
    theme = None if args.theme == "auto" else args.theme
    tty_out = os.dup(sys.stdout.fileno())
    saved = os.dup(1), os.dup(2)
    log = open(log_path(), "a", encoding="utf-8")  # noqa: SIM115 - lifetime spans the session
    try:
        # Anything printed by libraries (or native code) while the TUI owns the screen goes to the log.
        os.dup2(log.fileno(), 1)
        os.dup2(log.fileno(), 2)
        terminal = Terminal(fd_in=sys.stdin.fileno(), fd_out=tty_out, mouse=not args.no_mouse)
        app.run(terminal, theme_override=theme)
    finally:
        with contextlib.suppress(Exception):
            agent.close()
        os.dup2(saved[0], 1)
        os.dup2(saved[1], 2)
        for fd in (*saved, tty_out):
            with contextlib.suppress(OSError):
                os.close(fd)
        log.close()
    if args.demo:
        print(f"frond demo project left at {root}")
    return 0


def run_headless(
    args: argparse.Namespace,
    config: AgentConfig,
    workspace: Workspace,
    prompt: str,
    lm: dspy.LM | None,
    persist: Callable[[list[TurnRecord]], None] | None = None,
    restored: list[TurnRecord] | None = None,
    log_path: Path | None = None,
    world_dir: Path | None = None,
) -> int:
    from frond.agent.session import Agent
    from frond.printer import Printer

    if not prompt and not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()
    if not prompt:
        print("frond: no prompt given (pass one as an argument or on stdin)", file=sys.stderr)
        return 2
    from frond.agent.redact import Redactor

    printer = Printer(json_mode=args.json, verbose=args.verbose, redact=Redactor())  # its log may be uploaded
    agent = Agent(config, workspace, printer, lm=lm, sub_lm=lm, persist=persist, world_dir=world_dir)
    if log_path is not None:
        agent.attach_log(log_path)
    if restored:
        agent.restore(restored)
    try:
        record = agent.run_turn(prompt, {})
    except KeyboardInterrupt:
        agent.cancel()
        return 130
    finally:
        if args.export is not None:
            export_run(agent, args.export)
        agent.close()
    if record.status == "done":
        return 0
    return 75 if record.error_kind == "provider" else 1  # 75 (EX_TEMPFAIL): the provider failed, not the agent


def export_run(agent: Agent, directory: Path) -> None:
    """The run's full record, for harnesses such as Harbor: every message, step (reasoning, code, output) and
    answer as JSON lines, the token and cost totals, and the final answer."""
    import dataclasses
    import json

    from frond.agent.lm import usage_totals
    from frond.agent.metrics import call_records
    from frond.agent.redact import Redactor

    redact = Redactor()  # the record leaves frond (Harbor, results): no credential values in it (ledger B12)
    directory.mkdir(parents=True, exist_ok=True)
    # Everything here covers this process: its LM calls, and the steps it added after any it loaded (--continue).
    with open(directory / "steps.jsonl", "w", encoding="utf-8") as f:
        for record in agent.steps.records()[agent.steps.loaded :]:
            clean = dataclasses.replace(
                record, reasoning=redact(record.reasoning), code=redact(record.code), output=redact(record.output)
            )
            f.write(json.dumps(dataclasses.asdict(clean), ensure_ascii=False) + "\n")
    usage = {"model": agent.config.model, "sub_model": agent.config.sub_model, **usage_totals(agent.lm, agent.sub_lm)}
    (directory / "usage.json").write_text(redact.json(usage, indent=1))
    with open(directory / "calls.jsonl", "w", encoding="utf-8") as f:
        roles = [("main", agent.lm)] + ([("sub", agent.sub_lm)] if agent.sub_lm is not agent.lm else [])
        for role, lm in roles:
            branches = agent.metrics.branch_calls if lm is agent.lm else agent.metrics.sub_branch_calls  # F30
            for record in call_records(lm, role, branches):
                f.write(redact.json(record) + "\n")
    this_run = [r for r in agent.history if r.first_seq > agent.steps.loaded]
    metrics = {
        "config": dataclasses.asdict(agent.config),  # what the run was configured with, to check each arm's setup
        "turns": len(this_run),
        "steps": sum(r.steps for r in this_run),
        "continued_after_seq": agent.steps.loaded,
        "status": this_run[-1].status if this_run else "",
        "error_kind": this_run[-1].error_kind if this_run else "",  # "provider": not the agent's failure (G22)
        "scopes": {"opened": agent.scopes.opened, "closed": agent.scopes.closed, "abandoned": agent.scopes.abandoned},
        **agent.metrics.as_dict(),
    }
    (directory / "metrics.json").write_text(redact.json(metrics, indent=1))
    last = agent.history[-1] if agent.history else None
    (directory / "answer.md").write_text(redact((last.response or last.error or "") if last else ""), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
