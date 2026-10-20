# notion-markdown-sync

Claude Code plugin for two-way markdown sync with Notion via the Markdown API.

## Project Structure

```
.claude-plugin/          Plugin manifest + marketplace config
skills/notion-markdown-sync/
  SKILL.md               Core skill instructions (the brain of the plugin)
  scripts/               Python helpers (media handling, GFM preprocessing)
  references/            Notion API docs (enhanced markdown spec, property types)
  evals/                 Eval scenarios for testing skill behavior
```

## Key Files

- **`skills/notion-markdown-sync/SKILL.md`** — The core skill. This is what Claude reads to know how to push/pull/sync. All Notion API patterns, edge cases, and examples live here.
- **`skills/notion-markdown-sync/scripts/notion_preprocess.py`** — Auto-detecting GFM-to-Notion preprocessor. Safe to run on any markdown file.
- **`skills/notion-markdown-sync/scripts/notion_media.py`** — Media download (pull) and upload (push) handler.
- **`.claude-plugin/marketplace.json`** — Single source of truth for plugin version. Bump version here on every release.
- **`CHANGELOG.md`** — Keep a Changelog format. Prepend new entries, never modify old ones.

## Versioning

- **Single source of truth**: `.claude-plugin/marketplace.json` → `plugins[0].version`
- **Do NOT** set version in `plugin.json` (marketplace.json takes priority for relative-path plugins)
- **Format**: Semantic versioning (`MAJOR.MINOR.PATCH`)
  - PATCH: bug fixes, doc corrections
  - MINOR: new features, new conversions in preprocessor, new property types
  - MAJOR: breaking changes to frontmatter format or skill behavior

## Testing

Run evals to verify skill behavior:
```
skills/notion-markdown-sync/evals/evals.json
```
5 eval scenarios, 34 assertions covering push, pull, validate, media-pull, and media-push.

For the preprocessor, run unit tests:
```bash
python3 -c "
import sys; sys.path.insert(0, 'skills/notion-markdown-sync/scripts')
from notion_preprocess import preprocess, is_notion_format
# Add test cases here
"
```

## Commit Messages

Use conventional commit format:
```
<type>: <concise summary>

<optional body with details>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

## Release Workflow

Use the `/ship` skill or follow these steps manually:

1. Analyze changes (`git diff`)
2. Determine version bump (patch/minor/major)
3. Update `CHANGELOG.md` (prepend new entry)
4. Update version in `.claude-plugin/marketplace.json`
5. Commit: `chore: release vX.Y.Z`
6. Tag: `git tag -a vX.Y.Z -m "vX.Y.Z: <summary>"`
7. Push: `git push && git push --tags`
8. Create GitHub release: `gh release create vX.Y.Z --title "vX.Y.Z — <summary>" --notes "<body>"`

## Rules

- Never commit sensitive data (API keys, real page IDs, workspace names)
- All example UUIDs must be placeholder format (`a1b2c3d4-...`)
- Keep SKILL.md under 50KB — Claude needs to load it in context
- Notion API version is `2026-03-11` — update references if Notion releases a new version
- Scripts must work with Python 3.9+ (macOS system Python compatibility)
- `notion_preprocess.py` must be idempotent on Notion-format files (auto-detect and skip)
