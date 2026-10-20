---
name: ship
description: >
  Release workflow for the notion-markdown-sync plugin. Analyzes changes,
  drafts changelog entry, bumps version, commits, tags, pushes, and creates
  a GitHub release. Use when the user says "ship", "release", or "cut a release".
---

# Ship — Release Workflow

Automate the full release cycle for the notion-markdown-sync plugin.

## Step 1: Analyze the Diff

Run these commands to understand what changed:

```bash
git diff --stat
git diff
git status
git log --oneline -10
```

Read the current version from `.claude-plugin/marketplace.json` (`plugins[0].version`).
Read the first entry in `CHANGELOG.md` for format reference.

Summarize: what changed, which files, what's the impact.

## Step 2: Draft Changelog + Version

**Suggest a version bump** based on scope:
- **Patch** (x.y.Z): bug fixes, doc corrections, minor tweaks
- **Minor** (x.Y.0): new features, new GFM conversions, new property types supported
- **Major** (X.0.0): NEVER auto-suggest. Only if user explicitly requests.

**Draft a changelog entry** in Keep a Changelog format:
```markdown
## [X.Y.Z] - YYYY-MM-DD

One-line summary.

### Added / Changed / Fixed / Removed
- Bullet points describing each change
```

**Draft a commit message:**
```
chore: release vX.Y.Z

<one-line summary of what this release includes>
```

**Draft GitHub release:**
- Title: `vX.Y.Z — Short Description`
- Body:
```markdown
## What's New

- Bullet points of user-facing changes

## Files Changed

| File | Change |
|------|--------|
| `path/to/file` | Description |

---
Full changelog: [CHANGELOG.md](CHANGELOG.md)
```

Present all drafts to the user. Wait for confirmation before proceeding.

## Step 3: Apply Version Bump

After user confirms:

1. **Prepend** the new changelog entry to `CHANGELOG.md` (after the header, before the previous version)
2. **Update version** in `.claude-plugin/marketplace.json` → `plugins[0].version`
3. **Do NOT** update version in `plugin.json` (marketplace.json is the authority)

## Step 4: Wait for Push Confirmation

Show a summary of all changes and ask: "Ready to push and create the release?"

Do NOT proceed until the user explicitly says to push.

## Step 5: Execute Ship

1. Stage specific files: `git add <file1> <file2> ...` — **never** use `git add -A` or `git add .`
2. Commit with the approved message (use HEREDOC format)
3. Create annotated tag: `git tag -a vX.Y.Z -m "vX.Y.Z: <summary>"`
4. Pull with rebase: `git pull --rebase`
5. Push commits and tag: `git push && git push --tags`
6. Create GitHub release:
   ```bash
   gh release create vX.Y.Z --title "vX.Y.Z — <title>" --notes "$(cat <<'EOF'
   <release body>
   EOF
   )"
   ```
7. Print the release URL

## Rules

- NEVER commit or push without explicit user confirmation
- NEVER use `git add -A` or `git add .` — always stage specific files
- NEVER force-push
- Always `git pull --rebase` before push
- If push fails, diagnose the issue — don't retry blindly
- Changelog entries are prepended, never modify existing entries
- Version lives ONLY in `marketplace.json` — nowhere else
