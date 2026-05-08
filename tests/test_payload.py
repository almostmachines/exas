"""Unit tests for the flag-dict → API payload mapping."""

from __future__ import annotations

import pytest

from exa_cli.cli import build_payload


def base(**overrides):
    opts = {
        "query": "hello",
        "additional_query": (),
        "type": "auto",
        "category": None,
        "num": 10,
        "include_domain": (),
        "exclude_domain": (),
        "start_date": None,
        "end_date": None,
        "start_crawl_date": None,
        "end_crawl_date": None,
        "user_location": None,
        "moderation": None,
        "system_prompt": None,
        "text": True,
        "max_text_chars": None,
        "include_html": False,
        "verbosity": None,
        "highlights": False,
        "highlights_query": None,
        "summary": False,
        "summary_query": None,
        "livecrawl": None,
        "max_age_hours": None,
        "subpages": None,
        "subpage_target": (),
        "links": None,
        "image_links": None,
    }
    opts.update(overrides)
    return opts


def test_minimal_payload():
    p = build_payload(base())
    assert p["query"] == "hello"
    assert p["type"] == "auto"
    assert p["numResults"] == 10
    assert p["contents"] == {"text": True}


def test_no_text():
    p = build_payload(base(text=False))
    assert p["contents"] == {"text": False}


def test_highlights_simple():
    p = build_payload(base(highlights=True))
    assert p["contents"]["highlights"] is True


def test_highlights_with_query():
    p = build_payload(base(highlights=True, highlights_query="key advancements"))
    assert p["contents"]["highlights"] == {"query": "key advancements"}


def test_summary_with_query():
    p = build_payload(base(summary=True, summary_query="main developments"))
    assert p["contents"]["summary"] == {"query": "main developments"}


def test_summary_query_implies_summary():
    p = build_payload(base(summary_query="main developments"))
    assert p["contents"]["summary"] == {"query": "main developments"}


def test_summary_default_object():
    p = build_payload(base(summary=True))
    assert p["contents"]["summary"] == {}


def test_text_options_promote_to_object():
    p = build_payload(base(max_text_chars=2000, include_html=True, verbosity="standard"))
    assert p["contents"]["text"] == {
        "maxCharacters": 2000,
        "includeHtmlTags": True,
        "verbosity": "standard",
    }


def test_category_hyphen_to_space():
    p = build_payload(base(category="research-paper"))
    assert p["category"] == "research paper"


def test_domain_filters():
    p = build_payload(base(
        include_domain=("arxiv.org", "paperswithcode.com"),
        exclude_domain=("twitter.com",),
    ))
    assert p["includeDomains"] == ["arxiv.org", "paperswithcode.com"]
    assert p["excludeDomains"] == ["twitter.com"]


def test_date_normalisation():
    p = build_payload(base(start_date="2025-01-01", end_date="2025-12-31"))
    assert p["startPublishedDate"] == "2025-01-01T00:00:00.000Z"
    assert p["endPublishedDate"] == "2025-12-31T00:00:00.000Z"


def test_date_passthrough_iso():
    p = build_payload(base(start_date="2025-01-01T12:00:00.000Z"))
    assert p["startPublishedDate"] == "2025-01-01T12:00:00.000Z"


def test_extras():
    p = build_payload(base(links=3, image_links=2))
    assert p["contents"]["extras"] == {"links": 3, "imageLinks": 2}


def test_subpage_target_single_string():
    p = build_payload(base(subpages=1, subpage_target=("sources",)))
    assert p["contents"]["subpages"] == 1
    assert p["contents"]["subpageTarget"] == "sources"


def test_subpage_target_array():
    p = build_payload(base(subpages=2, subpage_target=("sources", "papers")))
    assert p["contents"]["subpageTarget"] == ["sources", "papers"]


def test_max_age_hours():
    p = build_payload(base(max_age_hours=24))
    assert p["contents"]["maxAgeHours"] == 24


def test_additional_queries():
    p = build_payload(base(additional_query=("a", "b")))
    assert p["additionalQueries"] == ["a", "b"]


def test_moderation_flag():
    on = build_payload(base(moderation=True))
    off = build_payload(base(moderation=False))
    none = build_payload(base(moderation=None))
    assert on["moderation"] is True
    assert off["moderation"] is False
    assert "moderation" not in none


def test_user_location_and_system_prompt():
    p = build_payload(base(user_location="US", system_prompt="prefer official"))
    assert p["userLocation"] == "US"
    assert p["systemPrompt"] == "prefer official"


def test_full_kitchen_sink():
    p = build_payload(base(
        type="deep",
        category="research-paper",
        num=25,
        include_domain=("arxiv.org",),
        start_date="2025-01-01",
        max_text_chars=1500,
        highlights_query="LLM training",
        summary_query="key findings",
        max_age_hours=168,
        subpages=1,
        subpage_target=("sources",),
        links=2,
    ))
    assert p["type"] == "deep"
    assert p["category"] == "research paper"
    assert p["numResults"] == 25
    assert p["includeDomains"] == ["arxiv.org"]
    assert p["startPublishedDate"] == "2025-01-01T00:00:00.000Z"
    c = p["contents"]
    assert c["text"] == {"maxCharacters": 1500}
    assert c["highlights"] == {"query": "LLM training"}
    assert c["summary"] == {"query": "key findings"}
    assert c["maxAgeHours"] == 168
    assert c["subpages"] == 1
    assert c["subpageTarget"] == "sources"
    assert c["extras"] == {"links": 2}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
