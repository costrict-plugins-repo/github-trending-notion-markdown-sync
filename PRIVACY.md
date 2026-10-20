# Privacy Policy

**notion-markdown-sync** is a Claude Code plugin maintained by VegaStack Inc.

## What this plugin is

This plugin is a set of instructions (a SKILL.md file) and helper scripts that teach Claude how to sync markdown files with Notion using the Notion Markdown API. It is **not** a service, server, or application.

## Data collection

**This plugin collects no data.** Specifically:

- **No telemetry** — The plugin does not phone home, track usage, or send analytics.
- **No credential storage** — Your Notion API key is read from your local environment variable (`$NOTION_API_KEY`) at runtime. The plugin never stores, logs, or transmits your credentials.
- **No user data storage** — The plugin does not maintain any database, server, or persistent storage.
- **No third-party services** — The plugin communicates only with the official Notion API (`api.notion.com`). No other external services are contacted.

## How authentication works

1. You create a Notion internal integration at [notion.so/profile/integrations](https://www.notion.so/profile/integrations/internal)
2. You store the token in your local shell environment (`export NOTION_API_KEY="..."`)
3. When you ask Claude to sync, Claude reads the token from your environment and calls the Notion API directly
4. The token travels directly from your machine to Notion's servers — it is never sent anywhere else

## What data flows where

| From | To | What | Why |
|---|---|---|---|
| Your machine | Notion API | Markdown content, page properties | To create/update/read Notion pages |
| Notion API | Your machine | Page content, media files | To download pages and media locally |

All communication is between your machine and `api.notion.com` over HTTPS. No data passes through VegaStack or any intermediary.

## Local files

The plugin reads and writes files only in directories you specify:
- Markdown files you ask to push or pull
- An `assets/` directory for downloaded media (next to your markdown files)
- YAML frontmatter added to your markdown files (sync metadata like page ID and timestamp)

## Helper scripts

The bundled Python scripts (`notion_media.py`, `notion_preprocess.py`) run locally on your machine. They do not make network requests except to `api.notion.com` (for media upload/download) and Notion's S3 CDN (for downloading media files).

## Changes to this policy

If this policy changes, the update will be committed to this repository with a clear changelog entry.

## Contact

For privacy questions: hello@vegastack.com
