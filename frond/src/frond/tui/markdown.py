"""Render the Markdown the agent writes (its final answers) as styled terminal lines."""

from __future__ import annotations

import re
from collections.abc import Callable

from frond.tui.highlight import highlight, language_for
from frond.tui.style import PLAIN, Style, Theme
from frond.tui.text import Line, Span, line_width, pad, sanitize, str_width, truncate, wrap

type LinkResolver = Callable[[str], str | None]

_INLINE = re.compile(
    r"(?P<code>(?P<ticks>`+)(?P<code_body>.+?)(?P=ticks))"
    r"|(?P<bold>\*\*(?P<bold_body>.+?)\*\*|__(?P<bold_body2>.+?)__)"
    r"|(?P<strike>~~(?P<strike_body>.+?)~~)"
    r"|(?P<italic>\*(?![\s*])(?P<italic_body>.+?)(?<![\s*])\*|(?<![\w])_(?![\s_])(?P<italic_body2>.+?)(?<![\s_])_(?![\w]))"
    r"|(?P<link>\[(?P<link_text>[^\]]+)\]\((?P<link_url>[^)\s]+)(?:\s+\"[^\"]*\")?\))"
    r"|(?P<auto><(?P<auto_url>https?://[^>\s]+)>)"
    r"|(?P<url>https?://[^\s<>()\[\]]+[^\s<>()\[\].,;:!?'\"*_`])"
)
_LIST_ITEM = re.compile(r"^(?P<indent>\s*)(?P<marker>[-*+]|\d{1,3}[.)])\s+(?P<body>.*)$")
_FENCE = re.compile(r"^(?P<indent>\s*)(?P<fence>`{3,}|~{3,})\s*(?P<info>[^`\s]*)[^`]*$")
_HEADING = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.*?)\s*#*\s*$")
_HR = re.compile(r"^\s{0,3}(?:(?:-\s*){3,}|(?:\*\s*){3,}|(?:_\s*){3,})$")
_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)*\|?\s*$")
_PATHLIKE = re.compile(r"^[\w.~/-]*[\w-]\.[A-Za-z0-9]{1,8}(?::\d+(?::\d+)?)?$")


class MarkdownRenderer:
    def __init__(self, theme: Theme, link_resolver: LinkResolver | None = None) -> None:
        self.theme = theme
        self.link_resolver = link_resolver

    # ── inline ───────────────────────────────────────────────────────────────

    def inline(self, text: str, base: Style = PLAIN) -> Line:
        t = self.theme
        out: Line = []
        pos = 0
        for m in _INLINE.finditer(text):
            if m.start() > pos:
                out.append(Span(text[pos : m.start()], base))
            if m.group("code"):
                body = m.group("code_body")
                if len(m.group("ticks")) == 1 or not body.startswith(" "):
                    body = body.strip() if body.strip() else body
                style = base + t.code_inline
                if self.link_resolver and _PATHLIKE.match(body):
                    url = self.link_resolver(body)
                    if url:
                        style = style + Style(link=url)
                out.append(Span(body, style))
            elif m.group("bold"):
                out.extend(self.inline(m.group("bold_body") or m.group("bold_body2") or "", base + Style(bold=True)))
            elif m.group("strike"):
                out.extend(self.inline(m.group("strike_body"), base + Style(strike=True, dim=True)))
            elif m.group("italic"):
                body = m.group("italic_body") or m.group("italic_body2") or ""
                out.extend(self.inline(body, base + Style(italic=True)))
            elif m.group("link"):
                url = m.group("link_url")
                out.extend(self.inline(m.group("link_text"), base + t.link + Style(link=url)))
            elif m.group("auto"):
                url = m.group("auto_url")
                out.append(Span(url, base + t.link + Style(link=url)))
            elif m.group("url"):
                url = m.group("url")
                out.append(Span(url, base + t.link + Style(link=url)))
            pos = m.end()
        if pos < len(text):
            out.append(Span(text[pos:], base))
        return out

    # ── blocks ───────────────────────────────────────────────────────────────

    def render(self, text: str, width: int) -> list[Line]:
        width = max(10, width)
        lines = sanitize(text).split("\n")
        out: list[Line] = []
        i = 0

        def blank() -> None:
            if out and out[-1]:
                out.append([])

        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()
            if not stripped:
                blank()
                i += 1
                continue
            fence = _FENCE.match(raw)
            if fence:
                marker = fence.group("fence")
                body: list[str] = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith(marker[0] * len(marker)):
                    body.append(lines[i])
                    i += 1
                i += 1  # closing fence (or end of text while streaming)
                blank()
                out.extend(self.code_block("\n".join(body), fence.group("info"), width))
                out.append([])
                continue
            heading = _HEADING.match(stripped)
            if heading:
                blank()
                level = len(heading.group("hashes"))
                style = self.theme.heading if level <= 2 else Style(bold=True)
                out.extend(wrap(self.inline(heading.group("text"), style), width))
                out.append([])
                i += 1
                continue
            if _HR.match(stripped):
                blank()
                out.append([Span("─" * min(width, 60), self.theme.faint)])
                out.append([])
                i += 1
                continue
            if "|" in stripped and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1]):
                rows = [stripped]
                i += 2
                while i < len(lines) and "|" in lines[i] and lines[i].strip():
                    rows.append(lines[i].strip())
                    i += 1
                blank()
                out.extend(self.table(rows, width))
                out.append([])
                continue
            if stripped.startswith(">"):
                quote: list[str] = []
                while i < len(lines) and lines[i].strip().startswith(">"):
                    quote.append(lines[i].strip()[1:].removeprefix(" "))
                    i += 1
                bar = [Span("│ ", self.theme.faint)]
                out.extend(
                    [*bar, *[Span(s.text, s.style + self.theme.quote) for s in q]]
                    for q in self.render("\n".join(quote), width - 2)
                )
                continue
            item = _LIST_ITEM.match(raw)
            if item:
                while i < len(lines):
                    m = _LIST_ITEM.match(lines[i])
                    if not m:
                        if lines[i].strip() and lines[i].startswith("  ") and out:
                            # continuation of the previous item
                            indent = len(lines[i]) - len(lines[i].lstrip())
                            out.extend(wrap(self.inline(lines[i].strip()), width, prefix=[Span(" " * min(indent, 12))]))
                            i += 1
                            continue
                        break
                    out.extend(self.list_item(m, width))
                    i += 1
                continue
            out.extend(wrap(self.inline(stripped), width))
            i += 1
        while out and not out[-1]:
            out.pop()
        return out

    def list_item(self, m: re.Match[str], width: int) -> list[Line]:
        t = self.theme
        depth = len(m.group("indent").expandtabs(4)) // 2
        marker = m.group("marker")
        body = m.group("body")
        indent = "  " * min(depth, 6)
        if marker[0].isdigit():
            bullet = [Span(indent), Span(marker if marker.endswith(".") else marker[:-1] + ".", t.muted), Span(" ")]
        else:
            glyph = ("•", "◦", "▪")[min(depth, 2)]
            bullet = [Span(indent), Span(glyph, t.accent), Span(" ")]
        task = re.match(r"^\[([ xX])\]\s+(.*)$", body)
        content: Line
        if task:
            done = task.group(1) != " "
            bullet = [Span(indent), Span("✓ " if done else "○ ", t.success if done else t.muted)]
            content = self.inline(task.group(2), Style(dim=True) if done else Style())
        else:
            content = self.inline(body)
        cont = [Span(" " * line_width(bullet))]
        return wrap(content, width, prefix=bullet, continuation=cont)

    def code_block(self, code: str, info: str, width: int) -> list[Line]:
        t = self.theme
        lang = language_for(info) if info else None
        panel = Style(bg=t.panel)
        rows = highlight(code.rstrip("\n"), lang, t.syntax, panel)
        out: list[Line] = []
        label = (info or "").strip()
        inner = width - 2
        for n, row in enumerate(rows):
            pieces = wrap(row, inner, continuation=[]) if line_width(row) > inner else [row]
            for piece in pieces:
                line = [Span(" ", panel), *piece]
                if n == 0 and piece is pieces[0] and label and line_width(piece) + str_width(label) + 3 <= inner:
                    line = pad(line, width - str_width(label) - 1, panel)
                    line += [Span(label, Style(bg=t.panel) + t.faint), Span(" ", panel)]
                out.append(pad(line, width, panel))
        if not out:
            out.append(pad([Span(" ", panel)], width, panel))
        return out

    def table(self, rows: list[str], width: int) -> list[Line]:
        t = self.theme
        cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
        ncols = max(len(r) for r in cells)
        cells = [r + [""] * (ncols - len(r)) for r in cells]
        widths = [max(str_width(r[c]) for r in cells) for c in range(ncols)]
        total = sum(widths) + 3 * (ncols - 1)
        if total > width:
            budget = max(4, (width - 3 * (ncols - 1)) // ncols)
            widths = [min(w, budget) for w in widths]
        out: list[Line] = []
        for idx, row in enumerate(cells):
            line: Line = []
            for c, cell in enumerate(row):
                style = Style(bold=True) if idx == 0 else Style()
                rendered = truncate(self.inline(cell, style), widths[c])
                line += pad(rendered, widths[c])
                if c < ncols - 1:
                    line.append(Span(" │ ", t.faint))
            out.append(line)
            if idx == 0:
                out.append([Span("─┼─".join("─" * w for w in widths), t.faint)])
        return out
