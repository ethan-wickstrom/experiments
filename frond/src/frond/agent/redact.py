"""Secrets out of everything frond writes for others to read: run exports and headless logs (ledger B12).

A step can print anything its commands see, and a benchmark run hands its record to Harbor, which may upload it, and
to the analysis, whose results are committed. Before any of that leaves frond, three kinds of text are replaced:
- the values of the environment's credential variables (named as ``shell.CREDENTIAL_NAME`` defines them), by name;
- strings shaped like the common API keys (Anthropic, OpenAI, GitHub, AWS, Slack, Google);
- passwords embedded in URLs (``user:secret@host``).
The interactive TUI is not redacted: it shows the user their own machine.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping

from frond.agent.shell import CREDENTIAL_IN_URL, CREDENTIAL_NAME

KEY_SHAPES = re.compile(
    r"\b(?:sk-ant-[A-Za-z0-9_-]{20,}"  # Anthropic
    r"|sk-(?:proj-)?[A-Za-z0-9_-]{20,}"  # OpenAI
    r"|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}"  # GitHub
    r"|AKIA[0-9A-Z]{16}"  # AWS access key ids
    r"|xox[abposr]-[A-Za-z0-9-]{10,}"  # Slack
    r"|AIza[0-9A-Za-z_-]{35})"  # Google
)
MIN_SECRET = 8  # shorter values ("on", "true", "1") would match ordinary text


class Redactor:
    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        env = os.environ if environ is None else environ
        found = {v: name for name, v in env.items() if CREDENTIAL_NAME.search(name) and len(v) >= MIN_SECRET}
        self._secrets = sorted(found.items(), key=lambda item: -len(item[0]))  # longest first, so none is left half

    def __call__(self, text: str) -> str:
        for value, name in self._secrets:
            if value in text:
                text = text.replace(value, f"[redacted ${name}]")
        text = KEY_SHAPES.sub("[redacted key]", text)
        return CREDENTIAL_IN_URL.sub("://[redacted]@", text)
