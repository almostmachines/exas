"""Click-based CLI for the Exa /search endpoint."""

from __future__ import annotations

import json
import sys
from typing import Any

import click
from rich.console import Console
from rich.json import JSON as RichJSON

from . import __version__, api, config, format as fmt

CATEGORY_MAP = {
    "company": "company",
    "research-paper": "research paper",
    "news": "news",
    "personal-site": "personal site",
    "financial-report": "financial report",
    "people": "people",
}

SEARCH_TYPES = ["neural", "fast", "auto", "deep-lite", "deep", "deep-reasoning", "instant"]
VERBOSITIES = ["compact", "standard", "full"]
LIVECRAWLS = ["never", "fallback", "preferred", "always"]


def _expand_date(date_str: str) -> str:
    """Accept YYYY-MM-DD or full ISO 8601; normalise to ISO 8601 Z."""
    if "T" in date_str:
        return date_str
    return f"{date_str}T00:00:00.000Z"


def build_payload(opts: dict[str, Any]) -> dict[str, Any]:
    """Pure flag-dict → API payload mapping. Tested separately from click."""
    payload: dict[str, Any] = {"query": opts["query"]}

    if opts.get("additional_query"):
        payload["additionalQueries"] = list(opts["additional_query"])
    if opts.get("type"):
        payload["type"] = opts["type"]
    if opts.get("category"):
        payload["category"] = CATEGORY_MAP[opts["category"]]
    if opts.get("num") is not None:
        payload["numResults"] = opts["num"]
    if opts.get("include_domain"):
        payload["includeDomains"] = list(opts["include_domain"])
    if opts.get("exclude_domain"):
        payload["excludeDomains"] = list(opts["exclude_domain"])
    if opts.get("start_date"):
        payload["startPublishedDate"] = _expand_date(opts["start_date"])
    if opts.get("end_date"):
        payload["endPublishedDate"] = _expand_date(opts["end_date"])
    if opts.get("start_crawl_date"):
        payload["startCrawlDate"] = _expand_date(opts["start_crawl_date"])
    if opts.get("end_crawl_date"):
        payload["endCrawlDate"] = _expand_date(opts["end_crawl_date"])
    if opts.get("user_location"):
        payload["userLocation"] = opts["user_location"]
    if opts.get("moderation") is not None:
        payload["moderation"] = opts["moderation"]
    if opts.get("system_prompt"):
        payload["systemPrompt"] = opts["system_prompt"]

    contents = _build_contents(opts)
    if contents:
        payload["contents"] = contents

    return payload


def _build_contents(opts: dict[str, Any]) -> dict[str, Any]:
    contents: dict[str, Any] = {}

    text_opts: dict[str, Any] = {}
    if opts.get("max_text_chars") is not None:
        text_opts["maxCharacters"] = opts["max_text_chars"]
    if opts.get("include_html"):
        text_opts["includeHtmlTags"] = True
    if opts.get("verbosity"):
        text_opts["verbosity"] = opts["verbosity"]

    text_flag = opts.get("text")
    if text_opts:
        contents["text"] = text_opts
    elif text_flag is True:
        contents["text"] = True
    elif text_flag is False:
        contents["text"] = False

    if opts.get("highlights_query"):
        contents["highlights"] = {"query": opts["highlights_query"]}
    elif opts.get("highlights"):
        contents["highlights"] = True

    summary_opts: dict[str, Any] = {}
    if opts.get("summary_query"):
        summary_opts["query"] = opts["summary_query"]
    if opts.get("summary") or summary_opts:
        contents["summary"] = summary_opts

    if opts.get("livecrawl"):
        contents["livecrawl"] = opts["livecrawl"]
    if opts.get("max_age_hours") is not None:
        contents["maxAgeHours"] = opts["max_age_hours"]
    if opts.get("subpages") is not None:
        contents["subpages"] = opts["subpages"]
    if opts.get("subpage_target"):
        targets = list(opts["subpage_target"])
        contents["subpageTarget"] = targets[0] if len(targets) == 1 else targets

    extras: dict[str, Any] = {}
    if opts.get("links") is not None:
        extras["links"] = opts["links"]
    if opts.get("image_links") is not None:
        extras["imageLinks"] = opts["image_links"]
    if extras:
        contents["extras"] = extras

    return contents


def _bail(msg: str, code: int = 1) -> None:
    click.echo(f"exas: {msg}", err=True)
    sys.exit(code)


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=False,
)
@click.version_option(__version__, prog_name="exas")
@click.pass_context
def main(ctx: click.Context) -> None:
    """A thorough CLI for the Exa /search endpoint."""
    cfg = config.load()
    ctx.obj = cfg
    if cfg.defaults:
        ctx.default_map = ctx.default_map or {}
        ctx.default_map.setdefault("search", {}).update(cfg.defaults)


@main.command()
@click.argument("query", nargs=-1, required=True)
@click.option("--additional-query", multiple=True, help="Extra query variations (deep-search variants).")
@click.option("-t", "--type", "search_type", type=click.Choice(SEARCH_TYPES), default="auto", show_default=True)
@click.option("--category", type=click.Choice(list(CATEGORY_MAP.keys())))
@click.option("-n", "--num", type=click.IntRange(1, 100), default=10, show_default=True)
@click.option("--include-domain", multiple=True, help="Restrict to these domains (repeatable).")
@click.option("--exclude-domain", multiple=True, help="Exclude these domains (repeatable).")
@click.option("--start-date", help="Earliest published date (YYYY-MM-DD or ISO 8601).")
@click.option("--end-date", help="Latest published date (YYYY-MM-DD or ISO 8601).")
@click.option("--start-crawl-date", help="Earliest crawl date.")
@click.option("--end-crawl-date", help="Latest crawl date.")
@click.option("--user-location", help="Two-letter ISO country code.")
@click.option("--moderation/--no-moderation", default=None, help="Filter unsafe content.")
@click.option("--system-prompt", help="Steer synthesised output / deep-search planning.")
@click.option("--text/--no-text", "text_flag", default=True, help="Return full page text. [default: on]")
@click.option("--max-text-chars", type=int, help="Cap text length per result.")
@click.option("--include-html", is_flag=True, help="Include HTML tags in text output.")
@click.option("--verbosity", type=click.Choice(VERBOSITIES), help="Text verbosity (requires --livecrawl always).")
@click.option("--highlights", is_flag=True, help="Return highlight snippets.")
@click.option("--highlights-query", help="Custom query that steers highlight selection.")
@click.option("--summary", is_flag=True, help="Return an LLM summary per result.")
@click.option("--summary-query", help="Custom query for the summary.")
@click.option("--livecrawl", type=click.Choice(LIVECRAWLS), help="(Deprecated upstream — prefer --max-age-hours.)")
@click.option("--max-age-hours", type=int, help="Use cached content younger than this; otherwise livecrawl.")
@click.option("--subpages", type=int, help="How many subpages per result to crawl.")
@click.option("--subpage-target", multiple=True, help="Term to find specific subpages (repeatable).")
@click.option("--links", type=int, help="Number of outbound links to return per result.")
@click.option("--image-links", type=int, help="Number of image links to return per result.")
@click.option("--json", "as_json", is_flag=True, help="Emit raw API JSON.")
@click.option("--show-cost", is_flag=True, help="Print costDollars.total to stderr.")
@click.option("--limit-chars", type=int, default=500, show_default=True, help="Per-result text truncation in pretty mode.")
@click.option("--timeout", type=float, default=api.DEFAULT_TIMEOUT, show_default=True, help="HTTP timeout in seconds.")
@click.pass_obj
def search(
    cfg: config.Config,
    query: tuple[str, ...],
    additional_query: tuple[str, ...],
    search_type: str,
    category: str | None,
    num: int,
    include_domain: tuple[str, ...],
    exclude_domain: tuple[str, ...],
    start_date: str | None,
    end_date: str | None,
    start_crawl_date: str | None,
    end_crawl_date: str | None,
    user_location: str | None,
    moderation: bool | None,
    system_prompt: str | None,
    text_flag: bool,
    max_text_chars: int | None,
    include_html: bool,
    verbosity: str | None,
    highlights: bool,
    highlights_query: str | None,
    summary: bool,
    summary_query: str | None,
    livecrawl: str | None,
    max_age_hours: int | None,
    subpages: int | None,
    subpage_target: tuple[str, ...],
    links: int | None,
    image_links: int | None,
    as_json: bool,
    show_cost: bool,
    limit_chars: int,
    timeout: float,
) -> None:
    """Run a search against Exa."""
    if not cfg.api_key:
        _bail(
            "no API key found. Set EXA_API_KEY or write one to "
            f"{config.config_path()} (run `exas config path` for the file location)."
        )

    opts: dict[str, Any] = {
        "query": " ".join(query),
        "additional_query": additional_query,
        "type": search_type,
        "category": category,
        "num": num,
        "include_domain": include_domain,
        "exclude_domain": exclude_domain,
        "start_date": start_date,
        "end_date": end_date,
        "start_crawl_date": start_crawl_date,
        "end_crawl_date": end_crawl_date,
        "user_location": user_location,
        "moderation": moderation,
        "system_prompt": system_prompt,
        "text": text_flag,
        "max_text_chars": max_text_chars,
        "include_html": include_html,
        "verbosity": verbosity,
        "highlights": highlights,
        "highlights_query": highlights_query,
        "summary": summary,
        "summary_query": summary_query,
        "livecrawl": livecrawl,
        "max_age_hours": max_age_hours,
        "subpages": subpages,
        "subpage_target": subpage_target,
        "links": links,
        "image_links": image_links,
    }

    payload = build_payload(opts)

    try:
        response = api.search(payload, api_key=cfg.api_key, timeout=timeout)
    except api.ExaError as e:
        _bail(str(e))

    if as_json:
        if sys.stdout.isatty():
            Console().print(RichJSON.from_data(response))
        else:
            json.dump(response, sys.stdout, indent=2)
            sys.stdout.write("\n")
    else:
        fmt.render(response, console=Console(), limit_chars=limit_chars)

    if show_cost:
        cost = response.get("costDollars", {}).get("total")
        if isinstance(cost, (int, float)):
            click.echo(f"cost: ${cost:.4f}", err=True)


@main.group(name="config")
def config_group() -> None:
    """Inspect the resolved exas config."""


@config_group.command("show")
@click.pass_obj
def config_show(cfg: config.Config) -> None:
    """Print resolved config (api key redacted)."""
    click.echo(f"config file:  {config.config_path()}")
    click.echo(f"key source:   {cfg.source}")
    click.echo(f"api_key:      {config.redact(cfg.api_key)}")
    if cfg.defaults:
        click.echo("defaults:")
        for k, v in cfg.defaults.items():
            click.echo(f"  {k} = {v!r}")
    else:
        click.echo("defaults:     <none>")


@config_group.command("path")
def config_path_cmd() -> None:
    """Print the path to the config file."""
    click.echo(str(config.config_path()))


if __name__ == "__main__":
    main()
