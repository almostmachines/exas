"""Pretty-print Exa search results to the terminal."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.markup import escape
from rich.padding import Padding
from rich.rule import Rule
from rich.text import Text


def _truncate(s: str, limit: int) -> str:
    s = s.strip()
    if limit <= 0 or len(s) <= limit:
        return s
    return s[: limit - 1].rstrip() + "…"


def _meta_line(result: dict[str, Any]) -> Text:
    parts: list[str] = []
    author = result.get("author")
    if isinstance(author, str) and author.strip():
        first = author.split(",")[0].strip()
        if first:
            parts.append(first)
    pub = result.get("publishedDate")
    if isinstance(pub, str) and pub:
        parts.append(pub[:10])
    return Text(" · ".join(parts), style="dim")


def render(response: dict[str, Any], *, console: Console, limit_chars: int = 500) -> None:
    results = response.get("results") or []
    if not results:
        console.print("[yellow]No results.[/yellow]")
        _footer(response, console)
        return

    for i, result in enumerate(results, 1):
        title = result.get("title") or "(untitled)"
        url = result.get("url") or ""

        header = Text()
        header.append(f"[{i}] ", style="bold cyan")
        header.append(title, style="bold")
        console.print(header)

        if url:
            console.print(Text(url, style=f"link {url} blue"), no_wrap=False)

        meta = _meta_line(result)
        if meta.plain:
            console.print(meta)

        body_blocks: list[tuple[str, str]] = []

        text = result.get("text")
        if isinstance(text, str) and text.strip():
            body_blocks.append(("", _truncate(text, limit_chars)))

        summary = result.get("summary")
        if isinstance(summary, str) and summary.strip():
            body_blocks.append(("Summary", _truncate(summary, limit_chars)))

        highlights = result.get("highlights")
        if isinstance(highlights, list) and highlights:
            joined = "\n".join(f"• {h.strip()}" for h in highlights if isinstance(h, str))
            if joined:
                body_blocks.append(("Highlights", _truncate(joined, limit_chars * 2)))

        for label, body in body_blocks:
            console.print()
            if label:
                console.print(Text(label, style="bold magenta"))
            console.print(Padding(escape(body), (0, 0, 0, 0)))

        console.print()

    _footer(response, console)


def _footer(response: dict[str, Any], console: Console) -> None:
    n = len(response.get("results") or [])
    search_type = response.get("resolvedSearchType") or response.get("searchType") or ""
    cost = response.get("costDollars", {}).get("total")
    bits = [f"{n} result{'s' if n != 1 else ''}"]
    if search_type:
        bits.append(f"{search_type} search")
    if isinstance(cost, (int, float)):
        bits.append(f"${cost:.4f}")
    console.print(Rule(Text(" · ".join(bits), style="dim"), style="dim"))
