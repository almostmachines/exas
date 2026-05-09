# exas

A thorough CLI for the [Exa](https://exa.ai) `/search` endpoint. Every flag in the OpenAPI spec is reachable; defaults stay close to the API's own defaults.

## Install

```sh
uv tool install /data/coding/python/exa-cli
```

This drops `exas` on `$PATH` (under `~/.local/bin`).

## Configure

Create `~/.config/exa/config.toml`:

```toml
api_key = "exa_..."

[defaults]
type = "auto"
num_results = 10
text = true
max_age_hours = 168
```

Or export `EXA_API_KEY` in your shell — it overrides the file.

```sh
exas config show   # check what's loaded
exas config path   # print the file location
```

## Use

```sh
# Pretty terminal output (default)
exas search "claude code release notes" -n 3 --highlights

# Raw JSON for scripting
exas search "arxiv RAG 2026" \
  --category research-paper \
  --start-date 2026-01-01 \
  --json

# Domain restriction + summary
exas search "openai blog" \
  --include-domain openai.com \
  --num 2 \
  --summary --summary-query "what was announced"

# Lowest-latency lookup
exas search "weather in Paris" --type instant --num 1
```

Run `exas search --help` for the full flag surface.

## Notes

- Search types: `neural`, `fast`, `auto` (default), `deep-lite`, `deep`, `deep-reasoning`, `instant`.
- Categories: `company`, `research-paper`, `news`, `personal-site`, `financial-report`, `people`. Note that `company` and `people` only support a limited filter set (no date/exclude-domain filters, etc.).
- Date flags accept `YYYY-MM-DD`, expanded to ISO 8601 internally.
- For freshness, prefer `--max-age-hours` over the deprecated `--livecrawl`.
- `--verbosity` requires `--livecrawl always` to take effect (per the API spec).
- The `contents.text` option becomes an object whenever `--max-text-chars`, `--include-html`, or `--verbosity` is set; otherwise it's the bare boolean.

## Develop

```sh
cd /data/coding/python/exa-cli
uv sync
uv run pytest
```

## LICENSE

[MIT](LICENSE)
