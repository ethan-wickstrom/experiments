"""Run frond on Terminal-Bench (and any other Harbor dataset) through Harbor's installed-agent interface.

    export ANTHROPIC_API_KEY=...
    PYTHONPATH=bench uvx --from harbor==0.25.0 harbor run -d terminal-bench/terminal-bench@4.0.0 \
        -a frond_harbor:Frond -m anthropic/claude-opus-5-5 -e docker -n 1 -o jobs

bench/matrix.py builds these commands for every arm of an experiment, with the egress-CA overlay a host that
re-terminates TLS needs (bench/compose/egress-ca.yaml).

Harbor runs each task in a sandbox container, by default with Docker; ``-e daytona``, ``modal`` and others work
without it. This adapter installs frond there from a wheel it builds from this checkout and uploads, so it needs
neither PyPI nor a public repository. It then runs ``frond -p --yolo`` on the task instruction and exports the
run's full record. That record becomes Harbor's ATIF trajectory: every REPL step is a tool call (its code) with its
observation (the output). Leaderboard review reads exactly that, and Harbor's viewer shows it. The tokens, cache
reads and cost reach Harbor's results.

This file is not part of the frond package and needs ``harbor`` (written against 0.25.0) to import.
"""

from __future__ import annotations

import json
import shlex
import subprocess
import tempfile
from pathlib import Path
from typing import Annotated, Any

from harbor.agents.agent_auth_resolution import ModelConnectionSpec, ProviderAccess
from harbor.agents.capabilities import AgentCapabilities
from harbor.agents.installed.base import BaseInstalledAgent, with_prompt_template
from harbor.agents.options import Cli, InstalledAgentOptions
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext
from harbor.models.trajectories import (
    Agent,
    FinalMetrics,
    Observation,
    ObservationResult,
    Step,
    ToolCall,
    Trajectory,
)
from pydantic import Field

PROJECT = Path(__file__).resolve().parents[1]  # the frond project this file ships with
PATH = 'export PATH="$HOME/.local/bin:$PATH"'
EXPORT = "frond"  # under Harbor's agent log directory: steps.jsonl, usage.json, calls.jsonl, metrics.json, answer.md
_wheel: Path | None = None


def build_wheel() -> Path:
    """Build frond's wheel once per process."""
    global _wheel
    if _wheel is None or not _wheel.exists():
        out = Path(tempfile.mkdtemp(prefix="frond-wheel-"))
        subprocess.run(["uv", "build", "--wheel", "--out-dir", str(out), str(PROJECT)], check=True, capture_output=True)
        _wheel = next(out.glob("frond-*.whl"))
    return _wheel


def trajectory(export: Path, *, version: str, model: str | None) -> Trajectory:
    """frond's exported record as an ATIF trajectory: messages, then one tool call per REPL step."""
    usage = _read_json(export / "usage.json")
    steps: list[Step] = []
    lines = (
        (export / "steps.jsonl").read_text(encoding="utf-8").splitlines() if (export / "steps.jsonl").is_file() else []
    )
    for line in lines:
        try:
            record = json.loads(line)
        except ValueError:
            continue
        step_id = len(steps) + 1
        extra = {"seq": record.get("seq"), "turn": record.get("turn")}
        if record.get("scope"):
            extra["scope"] = record["scope"]  # a sub-agent's step
        if record.get("kind") == "user":
            steps.append(Step(step_id=step_id, source="user", message=record.get("output", ""), extra=extra))
        elif record.get("kind") == "answer":
            steps.append(Step(step_id=step_id, source="agent", message=record.get("output", ""), extra=extra))
        else:
            call = f"step-{record.get('seq')}"
            steps.append(
                Step(
                    step_id=step_id,
                    source="agent",
                    model_name=model,
                    message=record.get("reasoning", ""),
                    tool_calls=[
                        ToolCall(tool_call_id=call, function_name="python", arguments={"code": record.get("code", "")})
                    ],
                    observation=Observation(
                        results=[ObservationResult(source_call_id=call, content=record.get("output", ""))]
                    ),
                    extra={**extra, "step": record.get("step"), "error": bool(record.get("error"))},
                )
            )
    if not steps:  # frond never started (installation or key problems): keep the trajectory valid
        steps.append(Step(step_id=1, source="agent", message="(frond produced no record)"))
    return Trajectory(
        agent=Agent(name="frond", version=version, model_name=model),
        steps=steps,
        final_metrics=FinalMetrics(
            total_prompt_tokens=usage.get("input_tokens"),
            total_completion_tokens=usage.get("output_tokens"),
            total_cached_tokens=usage.get("cache_read_tokens"),
            total_cost_usd=usage.get("cost_usd"),
            total_steps=sum(1 for s in steps if s.tool_calls),
        ),
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


class FrondOptions(InstalledAgentOptions):
    max_steps: Annotated[int | None, Cli("--max-steps")] = Field(
        default=None, description="REPL steps per turn before frond wraps up (frond's default: 40)"
    )
    sub_model: Annotated[str | None, Cli("--sub-model")] = Field(
        default=None, description="model for sub-queries and sub-agents (default: a smaller sibling)"
    )
    effort: Annotated[str | None, Cli("--effort")] = Field(
        default=None, description="the main model's reasoning effort: low, medium, high, xhigh, max (frond: high)"
    )
    layout: Annotated[str | None, Cli("--layout")] = Field(
        default=None, description="how each step sees the history: turns (frond's) or chat (DSPy's); H6"
    )
    freshness: Annotated[str | None, Cli("--freshness")] = Field(
        default=None, description="on: mark stale reads and guard overwrites; off: only count stale actions; H3"
    )
    arm: Annotated[str | None, Cli("--arm")] = Field(
        default=None,
        description="rlm: Python in a persistent REPL (frond's default); react: one tool call per step; H1",
    )
    fork: Annotated[int | None, Cli("--fork")] = Field(
        default=None, description="most branches a FORK may explore; 1 turns FORK off (frond's default); H2"
    )


class Frond(BaseInstalledAgent):
    capabilities = AgentCapabilities(atif=True)
    options_model = FrondOptions
    DEFAULT_SETUP_TIMEOUT_SEC = 600.0  # uv and a managed Python may need downloading
    MODEL_CONNECTION = ModelConnectionSpec(
        agent_provider_access=ProviderAccess(
            api_key_candidate_names=["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"]
        )
    )

    @staticmethod
    def name() -> str:
        return "frond"

    def get_version_command(self) -> str | None:
        return f"{PATH}; frond --version"

    async def install(self, environment: BaseEnvironment) -> None:
        wheel = build_wheel()
        await self.ensure_system_dependencies(environment, ("curl", "ca_certificates"))
        target = f"/tmp/{wheel.name}"
        await environment.upload_file(wheel, target)
        await self.exec_as_agent(
            environment,
            command=(
                "set -euo pipefail; "
                "command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh; "
                f"{PATH}; uv tool install --force --python 3.12 {shlex.quote(target)}; frond --version"
            ),
        )

    @with_prompt_template
    async def run(self, instruction: str, environment: BaseEnvironment, context: AgentContext) -> None:
        if not self.model_name:
            raise ValueError("frond needs a model: pass -m provider/name")
        logs = self.environment_logs_dir.as_posix()
        env = {**self.model_connection.env, "FROND_INSTRUCTION": instruction}
        await self.exec_as_agent(
            environment,
            env=env,
            command=(
                f'{PATH}; task="$FROND_INSTRUCTION"; unset FROND_INSTRUCTION; '
                f"frond -p --yolo --model {shlex.quote(self.model_name)} {self.build_cli_flags()} "
                f'--export {logs}/{EXPORT} "$task" </dev/null 2>{logs}/frond-progress.log; rc=$?; '
                # Harbor classifies failures (rate limits, auth) from stderr: give it the tail of frond's progress.
                f"tail -n 40 {logs}/frond-progress.log >&2; exit $rc"
            ),
        )

    def populate_context_post_run(self, context: AgentContext) -> None:
        export = self.logs_dir / EXPORT
        usage = _read_json(export / "usage.json")
        context.n_input_tokens = usage.get("input_tokens")
        context.n_cache_tokens = usage.get("cache_read_tokens")
        context.n_output_tokens = usage.get("output_tokens")
        context.cost_usd = usage.get("cost_usd")
        record = trajectory(export, version=self.version() or "unknown", model=self.model_name)
        (self.logs_dir / "trajectory.json").write_text(json.dumps(record.to_json_dict(), indent=2))
