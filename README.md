# notion-markdown-sync

Two-way markdown sync for Notion. Push local markdown files to Notion pages, pull Notion pages to local markdown, and keep them in sync — all through the [Notion Markdown API](https://developers.notion.com/guides/data-apis/working-with-markdown-content).

Built as a [Claude Code plugin](https://code.claude.com/docs/en/plugins) — works with Claude Code, Claude.ai, and Claude Cowork.

## Why This Plugin

We love Notion for organizing everything. We love writing in markdown — it's fast, portable, and lives in Git. And we love how AI agents like Claude Code work with markdown natively — reading, writing, and transforming text is what they're built for.

The problem? Getting markdown in and out of Notion has always been painful.

**The existing approach** — tools like [Notion MCP](https://developers.notion.com/guides/mcp/mcp) and the blocks API — works at the block level. Reading a page means paginating through blocks 50 at a time, fetching nested children separately, then reconstructing the content. Writing means batching blocks 100 at a time with nesting limitations. For a complex page, that adds up to dozens of API calls.

**This plugin uses Notion's Markdown API** — the entire page in a single call. A full push or pull takes **2-4 API calls** regardless of whether your page is 10 lines or 10,000 lines.

| Approach | Read a page | Write it back | Nested content |
|---|---|---|---|
| Blocks API / Notion MCP | Paginated (50 blocks/req) + separate child fetches | Batched (100 blocks/req) + nesting limits | Extra calls per level |
| **This plugin (Markdown API)** | **1 call** | **1 call** | **Included** |

Claude Code + markdown is a natural fit. Instead of fighting with block-level APIs and complex SDK setups, this plugin lets you just say *"push this doc to Notion"* — and Claude handles the rest.

We built this at [VegaStack](https://vegastack.com) because we sync dozens of docs between our repos and Notion daily. We open-sourced it because everyone deserves a better way to bridge markdown and Notion.

## Use Cases

### Publish docs from your repo to Notion

Keep your documentation in Git (where developers work) and push it to Notion (where everyone else reads it). PRDs, technical specs, architecture docs, runbooks, API references, onboarding guides — write in your editor, push to Notion.

```
Push docs/architecture.md to our "Engineering Wiki" database in Notion
```
```
Push the PRD at docs/prd-user-auth.md to Notion under the Product Specs page
```
```
Push all markdown files in docs/runbooks/ to the "Runbooks" database
```

### Pull Notion pages to local markdown

Download any Notion page as a clean markdown file. Edit in VS Code or Cursor, diff changes in Git, feed into Claude Code for analysis, or use as context for AI-assisted development.

```
Pull https://notion.so/My-Wiki-abc123 to local markdown at wiki/
```
```
Pull our API reference page from Notion to docs/api-reference.md
```
```
Pull the "Product Roadmap" database — save each page as a separate markdown file in docs/roadmap/
```

### Keep PRDs and specs in sync

Write a PRD, technical spec, or RFC locally, push to Notion for team review. Product and engineering collaborate in Notion, developers pull changes back to their repo. The sync metadata tracks what changed and where.

```
Sync docs/prd-user-auth.md with Notion
```
```
Sync docs/rfc-new-api.md — check if Notion version has changes from the team
```

### Convert GitHub-Flavored Markdown for Notion

Have existing docs from GitHub repos, Claude Code plans, or other markdown tools with pipe tables, `->` arrows, `> [!NOTE]` callouts? The plugin auto-detects and converts them to Notion's format — no manual reformatting.

```
Push README.md to Notion — it has GFM tables and callouts
```
```
Push my Claude Code plan at docs/plans/migration-plan.md to Notion for team review
```

### Manage Notion database pages from your editor

Push project docs to a Notion database — each file becomes a page with properties like Status, Owner, Sprint, and Priority managed from YAML frontmatter.

```
Push docs/features/ to the "Product Roadmap" database in Notion
```
```
Update the Status to "Done" and add tag "v2.1" for docs/features/dark-mode.md and push to Notion
```

### Bonus: automated Notion backups

Since this plugin produces clean markdown files, you can combine it with Git and CI/CD for automated Notion backups. Pair with a nightly GitHub Action that pulls your critical Notion databases to a `notion-backup/` branch — instant version history for your entire workspace. No more worrying about accidental deletions or workspace issues.

## Features

- **Push** — Create or update Notion pages from local markdown files
- **Pull** — Download Notion pages as clean local markdown with YAML frontmatter
- **Two-way sync** — Detect changes on both sides, resolve conflicts
- **GFM auto-preprocessing** — Automatically converts GitHub-Flavored Markdown (pipe tables, arrows, callouts) to Notion's enhanced format
- **Media handling** — Download Notion media locally on pull, upload local images on push
- **Database pages** — Full support for Notion database properties (select, multi-select, date, people, relations, etc.)
- **Icon replication** — Preserves page icons (emoji, external URLs, custom emoji) on push and pull
- **Validation** — Check markdown files for Notion compatibility before pushing
- **Round-trip fidelity** — 100% content preservation on pull-push-pull cycles

## Quickstart

### 1. Install the plugin

**From the plugin marketplace:**
```bash
# In Claude Code, open the plugin manager
/plugin marketplace add vegastack/oss-notion-markdown-sync
/plugin install notion-markdown-sync@vegastack-oss-notion-markdown-sync
```

**Manual install:**
```bash
git clone https://github.com/vegastack/oss-notion-markdown-sync.git
claude --plugin-dir ./notion-markdown-sync
```

### 2. Set up your Notion API key

Create an internal integration at [notion.so/profile/integrations](https://www.notion.so/profile/integrations/internal), then add the token to your shell:

```bash
# Add to ~/.zshrc or ~/.bashrc
export NOTION_API_KEY="ntn_your_token_here"
```

Grant the integration access to your pages: open the page in Notion > `...` menu > `Connections` > add your integration.

### 3. Start syncing

Just ask Claude in plain English:

```
Push docs/roadmap.md to Notion under page <page-id>
```
```
Pull this Notion page to local: https://notion.so/My-Page-abc123
```
```
Sync docs/guide.md with Notion
```

## How Each Operation Works

### Push (local to Notion)

```
Push /path/to/document.md to Notion as a new page under <parent-page-id>
```

What happens:
1. Auto-detects if the file is standard markdown or Notion-enhanced format
2. Converts GFM syntax if needed (tables, arrows, callouts, code blocks)
3. Creates or updates the page via the Markdown API
4. Saves sync metadata (page ID, URL, timestamp) to the file's YAML frontmatter

### Pull (Notion to local)

```
Pull Notion page https://notion.so/My-Page-abc123 to docs/my-page.md
```

What happens:
1. Fetches page content and properties via the Markdown API
2. Downloads embedded images and files to a local `assets/` directory
3. Writes the markdown file with YAML frontmatter containing sync metadata

### Push to a database

```
Push docs/meeting-notes.md to the "Meeting Notes" database <database-id>
```

Database properties are stored in YAML frontmatter and synced both ways:

```yaml
---
notion_page_id: "abc123..."
notion_parent_type: "database"
title: "Q1 Planning Meeting"
notion_properties:
  Status: "In Progress"
  Priority: "High"
  Tags: ["Planning", "Q1"]
  Due date: "2026-03-20"
  Assignee:
    - name: "Ada Lovelace"
      id: "user-uuid"
---

Your meeting notes content here...
```

### Validate

```
Validate docs/guide.md for Notion compatibility
```

Reports issues like unsupported heading levels (H5/H6), incorrect indentation, multi-line quote formatting, and unsupported block types — before you push.

### Sync status

```
Check Notion sync status for all markdown files in docs/
```

Scans for files with sync metadata and reports which are synced, modified, or untracked.

## GFM Auto-Preprocessing

Standard GitHub-Flavored Markdown is automatically converted to Notion's enhanced format before pushing. The preprocessor auto-detects the format — files already in Notion format pass through unchanged.

| GFM syntax | Converted to | Why |
|---|---|---|
| `->`, `<-`, `=>` | `→`, `←`, `⇒` | Notion escapes `>` and `<` to `\>` and `\<` |
| `--` (standalone) | `—` (em dash) | Proper typography |
| `~10` (approx) | `\~10` | Prevents strikethrough interpretation |
| Pipe tables | `<table>` HTML | Avoids content corruption in table cells |
| Unlabeled ` ``` ` code blocks | ` ```plain text ` | Prevents Notion from guessing wrong language |
| `> [!NOTE]` callouts | `<callout>` tags | GFM callout syntax not supported by Notion |
| Multi-line `> ` quotes | Single `> ` with `<br>` | Multiple `>` lines create separate quote blocks |
| Bare `file.sh` names | `` `file.sh` `` | Prevents Notion from auto-linking as domains |

## Authentication and Security

This plugin **never stores, logs, or transmits your credentials**. It's a set of instructions — not a service. Your Notion API token stays in your local environment and goes directly from your machine to Notion's API over HTTPS. Nothing passes through any intermediary. See [PRIVACY.md](PRIVACY.md) for full details.

### Setup

1. Create an internal integration at [notion.so/profile/integrations](https://www.notion.so/profile/integrations/internal)
2. Store the token using one of these methods:

**Shell profile** (recommended for most users):
```bash
# Add to ~/.zshrc or ~/.bashrc
export NOTION_API_KEY="ntn_your_token_here"
```

**`.env` file** (for project-specific tokens):
```bash
# Make sure .env is in your .gitignore!
NOTION_API_KEY=ntn_your_token_here
```

**macOS Keychain** (most secure):
```bash
# Store the token
security add-generic-password -a "$USER" -s "notion-api-key" -w "ntn_your_token_here"

# Retrieve it automatically (add to ~/.zshrc)
export NOTION_API_KEY=$(security find-generic-password -a "$USER" -s "notion-api-key" -w)
```

3. Grant the integration access: open the Notion page/database > `...` menu > `Connections` > add your integration

## How It Works Under the Hood

Built on Notion's [Markdown API](https://developers.notion.com/guides/data-apis/working-with-markdown-content) (v2026-03-11).

**Push flow:**
```
Local .md file
  → Auto-preprocess (converts GFM to Notion format if needed)
  → Strip YAML frontmatter
  → Strip leading H1 (title is set via page properties)
  → POST or PATCH via Markdown API
  → Update local frontmatter with sync metadata (page ID, URL, timestamp)
```

**Pull flow:**
```
GET /v1/pages/:id/markdown (fetch content)
  → GET /v1/pages/:id (fetch title, icon, properties)
  → Prepend # H1 title to markdown
  → Add YAML frontmatter with sync metadata
  → Download media to local assets/ directory
  → Write .md file
```

**Sync flow:**
```
Pull current Notion content → Compare with local file (ignoring frontmatter)
  → If only local changed: push to Notion
  → If only Notion changed: update local file
  → If both changed: show diff, ask user which to keep
```

## Plugin Structure

```
notion-markdown-sync/
├── .claude-plugin/
│   ├── plugin.json                          # Plugin manifest
│   └── marketplace.json                     # Marketplace catalog
├── skills/
│   └── notion-markdown-sync/
│       ├── SKILL.md                         # Core skill instructions
│       ├── scripts/
│       │   ├── notion_media.py              # Media upload/download handler
│       │   └── notion_preprocess.py         # GFM auto-detection + preprocessor
│       ├── references/
│       │   ├── enhanced-markdown-format.md  # Notion enhanced markdown spec
│       │   ├── working-with-markdown-content.md  # Markdown API guide
│       │   ├── notion-page-property-types.md     # Database property types
│       │   └── sample-page-test-results.md       # H1/title behavior tests
│       └── evals/
│           └── evals.json                   # 5 eval scenarios, 34 assertions
├── PRIVACY.md
├── README.md
├── LICENSE
└── .gitignore
```

## Known Limitations

| Limitation | Details |
|---|---|
| **Mermaid display mode** | Newly created mermaid blocks default to code view. The preview toggle is a Notion UI-only setting, not accessible via API. |
| **Blank lines** | Notion strips blank lines between blocks. Use `<empty-block/>` in Notion-format files to preserve intentional spacing. |
| **Bold + inline code** | `**\`code\`**` renders with extra `****` markers in Notion (platform behavior). |
| **Media URL expiry** | Notion media URLs expire after ~1 hour. The media handler downloads files locally on pull to preserve them permanently. |

## Requirements

- [Claude Code](https://claude.com/claude-code) v1.0.33+ (or Claude.ai / Claude Cowork with plugin support)
- A Notion internal integration token ([create here](https://www.notion.so/profile/integrations/internal))
- Python 3.9+ (for media handling and GFM preprocessing scripts)

## Contributing

Contributions are welcome! To get started:

1. Fork the repo
2. Create a feature branch
3. Test your changes with the included evals (`skills/notion-markdown-sync/evals/evals.json`)
4. Submit a pull request

## License

[MIT](LICENSE)

---

*This plugin is not affiliated with, endorsed by, or sponsored by Notion Labs, Inc. "Notion" is a trademark of Notion Labs, Inc. This plugin uses the public [Notion API](https://developers.notion.com/).*
