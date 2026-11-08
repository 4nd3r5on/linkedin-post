# linkedin-post

A wrapper around [mcp-server-linkedin](https://github.com/stickerdaniel/linkedin-mcp-server)
(Apache-2.0) that adds two tools: `create_post` and `delete_post`. MIT licensed.

It isn't a fork. The upstream package is a pinned dependency (`==4.29.0`) and runs
unchanged. This project only registers extra tools next to upstream's.

## Features

- All upstream tools (profiles, jobs, feed, messaging, ...) work as before.
- `create_post(text, confirm_post)` publishes a text post to your feed.
  - `confirm_post: false` is a dry run: the text is inserted and then the draft is discarded.
  - The post goes out with the share dialog's current audience (normally "Anyone"),
    and the result reports which one was used.
  - The result's `status` is `posted`, `dry_run`, `outcome_unknown`, `invalid_text`,
    `editor_not_found` or `insert_failed`. `retry_safe: false` means Post was
    clicked, so check the feed before calling again.
  - On a failure, `trace_dir` points at upstream's trace run (screenshot, URL, page
    title) under `~/.linkedin-mcp/trace-runs/`. `LINKEDIN_TRACE_MODE=off` disables it.
- `delete_post(post, confirm_delete)` deletes one of your own posts. This can't be undone.
  - `post` is a post URL (including `post_url` from `create_post`) or a URN like
    `urn:li:activity:<id>`.
  - `confirm_delete: false` is a dry run that only checks the post exists and is yours.
  - It uses the post's "..." menu and LinkedIn's own confirmation. Someone else's post
    returns `not_deletable`.

## Architecture

Hexagonal (ports and adapters):

```
src/linkedin_post/
  domain/
    entities/        PostText (validate + normalize), PostRef (URL/URN -> post page),
                     PublishResult / DeleteResult (status, posted/deleted, retry_safe)
    ports/primary/   Posting: create_post, delete_post
    ports/secondary/ SessionGate, PostComposer, PostRemover
    services/        PostingService: validate first, open the browser only for valid input
  adapters/
    primary/         FastMCP tools (create_post, delete_post)
    secondary/       upstream session gate, share-dialog composer, post remover, failure trace
  composition/       wiring, and the hook that adds our tools next to upstream's post tools
  common/            LinkedIn URLs
tests/               domain, service (with fake ports), MCP tools, remover in Chromium,
                     upstream hook
```

What comes from upstream instead of our own code:

- **Session:** signed-in Patchright browser (`get_ready_extractor`, `get_or_create_browser`).
- **Text rules:** `normalize_message_text` and `_refused_character`.
- **Post URL/URN parsing:** `feed_payload.permalink_paths_from_payload`.
- **Failure diagnostics:** `debug_trace.record_page_trace` and `mark_trace_for_retention`.
- **Error handling:** `tool_errors`.
- **Text insertion:** `execCommand('insertText')`, adapted from upstream's
  `message_sender.py` (Apache-2.0).
- **No private APIs:** no Voyager calls and no cookie replay, only the real web UI.

This relies on internal upstream names, so the version is pinned. Re-check
`composition/upstream.py` and the adapters before bumping it; `uv run pytest` checks the hook.

## Development

```sh
uv sync
uv run ruff check .          # every ruff rule (select = ["ALL"]), see pyproject.toml
uv run ruff format --check .
uv run pytest                # the remover test runs in a headless Chromium
```

With Nix, `nix develop` gives Python 3.12, uv and ruff, and runs `uv sync` for you.

CI (`.github/workflows/ci.yml`) runs the same on Python 3.12, 3.13 and 3.14. Ruff is
pinned because `ALL` picks up new rules on every upgrade; bump it on purpose and fix
what it finds.

## Setup

Replace the original `linkedin` server. Only one process can own the browser profile,
and a second copy would forward its tools to the first one without `create_post`.

```sh
claude mcp remove linkedin -s user
claude mcp add linkedin -s user -- uv run --directory ~/Projects/linkedin-post linkedin-post-mcp --no-auto-import
```

Then reconnect with `/mcp`.

## Remove

Restore the original server:

```sh
claude mcp remove linkedin -s user
claude mcp add linkedin -s user -e UV_HTTP_TIMEOUT=300 -- uvx mcp-server-linkedin@latest --no-auto-import
```
