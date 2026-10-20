# Title vs H1 Behavior — Test Results

## Key Finding

The Notion page title (`properties.title` or `properties.Name` for database pages) is **completely separate** from H1 headings in the body markdown. They are independent concepts.

## How Notion Handles the First H1 on Push

When you send markdown to `POST /v1/pages`, Notion applies this rule:

**The first `# H1` is consumed as the page title and stripped from the body IF AND ONLY IF:**
1. The H1 is the very first block (no blank lines or paragraphs before it)
2. It is the **only** H1 in the entire markdown body

If either condition fails (multiple H1s, or H1 not first), no H1 is consumed — they all stay in the body.

## Test Results

| Test | props.title sent | H1s in body | H1 position | Title result | H1s returned in body |
|------|-----------------|-------------|-------------|-------------|---------------------|
| 1 | Explicit (differs from H1) | 1 | First line | Explicit title | 0 — H1 STRIPPED |
| 2 | Explicit | 0 | N/A | Explicit title | 0 |
| 3 | None | 1 | First line | Auto-extracted from H1 | 0 — H1 STRIPPED |
| 4 | Explicit | 3 | First + others | Explicit title | 3 — ALL KEPT |
| 5 | None | 3 | First + others | "" (empty) | 3 — ALL KEPT |
| 6 | Explicit | 0 | N/A | Explicit title | 0 |
| 7 | Explicit | 2 | First + later | Explicit title | 2 — ALL KEPT |
| 8 | None | 2 | First + later | "" (empty) | 2 — ALL KEPT |
| 9 | Explicit (same as H1) | 1 | First line | Explicit title | 0 — H1 STRIPPED |
| 10 | None | 1 | Not first (paragraph before) | "" (empty) | 1 — KEPT |
| 11 | Explicit (differs from H1) | 1 | First line | Explicit title | 0 — H1 STRIPPED |

## Round-Trip Implications

### Push
- Always set `properties.title` explicitly
- If the file has a single leading H1, Notion will strip it from the body (it becomes the title)
- If the file has multiple H1s, none are stripped

### Pull
- The page title is NEVER included as an H1 in the returned markdown
- To restore round-trip fidelity: fetch the title from `GET /v1/pages/:id` and prepend `# {title}\n\n` to the markdown **if** the markdown doesn't already start with `# `

### Database Pages
- Title is in the property with `id: "title"` (property name varies — commonly `Name`, `Title`, etc.)
- The same H1 stripping rules apply to database page content

## Sample Page Test (Database Page)

Page ID: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
Parent: database `f9e8d7c6-b5a4-3210-fedc-ba0987654321`

Title property (`Name`): "Sample Title of the Page"

Body markdown returned:
```
# H1 Heading 1
These are a `code` blocks! [https://example.com](https://example.com)
```shell
# testing
sudo apt-get update
sudo apt install git
```
# H2 Heading
testing
```

Two H1s in body → neither consumed as title → title stays in properties only.
