"""Fetching documentation pages for the agent and turning HTML into readable text (stdlib only)."""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from html.parser import HTMLParser

USER_AGENT = "frond/0.1 (+https://github.com/ethan-wickstrom/experiments) python-urllib"
_BLOCK = frozenset(
    {
        "p",
        "div",
        "section",
        "article",
        "header",
        "footer",
        "main",
        "nav",
        "aside",
        "table",
        "tr",
        "ul",
        "ol",
        "dl",
        "dt",
        "dd",
        "blockquote",
        "figure",
        "figcaption",
        "form",
        "br",
        "hr",
    }
)
_SKIP = frozenset({"script", "style", "noscript", "svg", "template", "iframe", "head"})


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.skip = 0
        self.pre = 0
        self.href: str | None = None
        self.link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP:
            self.skip += 1
        if self.skip:
            return
        if tag in _BLOCK:
            self.out.append("\n")
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.out.append("\n" + "#" * int(tag[1]) + " ")
        elif tag == "li":
            self.out.append("\n- ")
        elif tag == "pre":
            self.pre += 1
            self.out.append("\n```\n")
        elif tag == "code" and not self.pre:
            self.out.append("`")
        elif tag == "a":
            self.href = dict(attrs).get("href")
            self.link_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag == "pre":
            self.pre = max(0, self.pre - 1)
            self.out.append("\n```\n")
        elif tag == "code" and not self.pre:
            self.out.append("`")
        elif tag == "a" and self.href is not None:
            text = "".join(self.link_text).strip()
            if text and self.href.startswith(("http://", "https://")):
                self.out.append(f" ({self.href})")
            self.href = None
        elif tag in _BLOCK or tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.out.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip:
            return
        if self.href is not None:
            self.link_text.append(data)
        self.out.append(data if self.pre else re.sub(r"\s+", " ", data))


def html_to_text(html: str) -> str:
    parser = _Text()
    parser.feed(html)
    parser.close()
    text = "".join(parser.out)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def fetch_text(url: str, *, timeout: float = 20.0, max_bytes: int = 5_000_000) -> tuple[str, str]:
    """Return (content_type, text) for ``url``. HTML is converted to text; other text types pass through."""
    if not url.startswith(("http://", "https://")):
        raise ValueError("fetch() only supports http:// and https:// URLs")
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/*;q=0.9,*/*;q=0.5"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            ctype = response.headers.get("Content-Type", "")
            charset = response.headers.get_content_charset() or "utf-8"
            raw = response.read(max_bytes + 1)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} {exc.reason} for {url}") from None
    except urllib.error.URLError as exc:
        raise RuntimeError(f"could not reach {url}: {exc.reason}") from None
    body = raw[:max_bytes].decode(charset, errors="replace")
    if "html" in ctype or body.lstrip()[:15].lower().startswith(("<!doctype html", "<html")):
        return ctype, html_to_text(body)
    return ctype, body
