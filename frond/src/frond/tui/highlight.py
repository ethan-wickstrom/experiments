"""Small regex-based syntax highlighters.

They tolerate incomplete input (code that is still streaming in), which rules out real parsers, and they
only need to make code easy to scan, not to be exact.
"""

from __future__ import annotations

import functools
import re

from frond.tui.style import PLAIN, Style
from frond.tui.text import Line, Span, sanitize

_PY_KEYWORDS = (
    "False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|"
    "global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield|match|case"
)
_PY_BUILTINS = (
    "print|len|range|open|str|int|float|list|dict|set|tuple|bool|bytes|isinstance|issubclass|enumerate|zip|map|"
    "filter|sorted|reversed|sum|min|max|any|all|repr|super|self|cls|type|object|getattr|setattr|hasattr|iter|next|"
    "abs|round|divmod|hash|id|input|vars|dir|callable|format|frozenset|slice|Exception|ValueError|TypeError|"
    "KeyError|RuntimeError|SUBMIT|view|read|write|edit|patch|delete|move|ls|glob|grep|sh|jobs|job_output|"
    "job_kill|plan|fetch|subagent|subagent_batched|llm_query|llm_query_batched"
)
_STRING = (
    r"(?:\b[rRbBuUfF]{1,2})?(?:\"\"\"[\s\S]*?(?:\"\"\"|\Z)|'''[\s\S]*?(?:'''|\Z)|"
    r"\"(?:\\.|[^\"\\\n])*(?:\"|$)|'(?:\\.|[^'\\\n])*(?:'|$))"
)
_NUMBER = r"\b(?:0[xX][\da-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+|\d[\d_]*(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?j?)\b"

_LANGS: dict[str, list[tuple[str, str]]] = {
    "python": [
        ("comment", r"#[^\n]*"),
        ("string", _STRING),
        ("decorator", r"(?m:^\s*@[\w.]+)"),
        ("number", _NUMBER),
        ("keyword", rf"\b(?:{_PY_KEYWORDS})\b"),
        ("builtin", rf"\b(?:{_PY_BUILTINS})\b"),
        ("function", r"\b[A-Za-z_]\w*(?=\s*\()"),
        ("type", r"\b[A-Z][A-Za-z0-9_]*\b"),
        ("operator", r"[=+\-*/%<>!&|^~:@]+"),
    ],
    "shell": [
        ("comment", r"(?m:(?:^|(?<=\s))#[^\n]*)"),
        ("string", r"\"(?:\\.|[^\"\\])*(?:\"|$)|'[^']*(?:'|$)"),
        ("variable", r"\$\{[^}]*\}|\$[A-Za-z_]\w*|\$[0-9@#?*!$-]"),
        ("keyword", r"\b(?:if|then|else|elif|fi|for|while|until|do|done|case|esac|in|function|return|export|local)\b"),
        ("function", r"(?m:(?:^|(?<=[|;&]\s)|(?<=[|;&])|(?<=&&\s)|(?<=\|\|\s))\s*[\w./-]+)"),
        ("constant", r"(?<=\s)--?[\w-]+"),
        ("operator", r"&&|\|\||[|;&<>]+"),
    ],
    "json": [
        ("type", r"\"(?:\\.|[^\"\\])*\"(?=\s*:)"),
        ("string", r"\"(?:\\.|[^\"\\])*(?:\"|$)"),
        ("number", r"-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b"),
        ("keyword", r"\b(?:true|false|null)\b"),
    ],
    "generic": [
        ("comment", r"//[^\n]*|/\*[\s\S]*?(?:\*/|\Z)|(?m:^\s*#(?!include|define|if|endif|pragma)[^\n]*)"),
        ("string", r"`(?:\\.|[^`\\])*(?:`|\Z)|\"(?:\\.|[^\"\\\n])*(?:\"|$)|'(?:\\.|[^'\\\n])*(?:'|$)"),
        ("number", _NUMBER),
        (
            "keyword",
            r"\b(?:fn|func|function|def|let|const|var|mut|pub|impl|trait|struct|enum|interface|type|class|extends|"
            r"implements|return|if|else|for|while|loop|match|switch|case|break|continue|import|export|from|package|"
            r"use|mod|as|new|this|self|async|await|yield|try|catch|throw|finally|static|public|private|protected|"
            r"void|null|nil|true|false|undefined|in|of|where|go|defer|select|chan|range|#include|#define)\b",
        ),
        ("function", r"\b[A-Za-z_]\w*(?=\s*\()"),
        ("type", r"\b[A-Z][A-Za-z0-9_]*\b"),
        ("operator", r"[=+\-*/%<>!&|^~:?]+"),
    ],
}

ALIASES = {
    "py": "python",
    "python3": "python",
    "py3": "python",
    "pyi": "python",
    "sh": "shell",
    "bash": "shell",
    "zsh": "shell",
    "console": "shell",
    "shell-session": "shell",
    "fish": "shell",
    "json": "json",
    "jsonc": "json",
    "jsonl": "json",
}
EXTENSIONS = {
    ".py": "python",
    ".pyi": "python",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".json": "json",
    ".js": "generic",
    ".ts": "generic",
    ".tsx": "generic",
    ".jsx": "generic",
    ".go": "generic",
    ".rs": "generic",
    ".java": "generic",
    ".c": "generic",
    ".h": "generic",
    ".cpp": "generic",
    ".cs": "generic",
    ".swift": "generic",
    ".kt": "generic",
    ".rb": "generic",
    ".php": "generic",
    ".scala": "generic",
    ".toml": "generic",
    ".yaml": "generic",
    ".yml": "generic",
    ".css": "generic",
    ".html": "generic",
    ".sql": "generic",
}


def language_for(name: str | None) -> str | None:
    if not name:
        return None
    key = name.strip().lower()
    if key in _LANGS:
        return key
    if key in ALIASES:
        return ALIASES[key]
    dot = key.rfind(".")
    if dot != -1:
        return EXTENSIONS.get(key[dot:])
    return "generic" if key else None


@functools.lru_cache(maxsize=16)
def _compiled(lang: str) -> re.Pattern[str]:
    parts = [f"(?P<{name}>{pattern})" for name, pattern in _LANGS[lang]]
    return re.compile("|".join(parts))


def highlight(code: str, lang: str | None, palette: dict[str, Style], base: Style = PLAIN) -> list[Line]:
    """Highlight ``code`` and split it into lines of styled spans (styles overlaid on ``base``)."""
    code = sanitize(code)
    lines: list[Line] = [[]]

    def emit(text: str, style: Style) -> None:
        first = True
        for piece in text.split("\n"):
            if not first:
                lines.append([])
            first = False
            if piece:
                lines[-1].append(Span(piece, style))

    if lang is None or lang not in _LANGS:
        emit(code, base)
        return lines
    pattern = _compiled(lang)
    pos = 0
    for m in pattern.finditer(code):
        if m.start() > pos:
            emit(code[pos : m.start()], base)
        kind = m.lastgroup or ""
        emit(m.group(), base + palette.get(kind, Style()))
        pos = m.end()
    if pos < len(code):
        emit(code[pos:], base)
    return lines
