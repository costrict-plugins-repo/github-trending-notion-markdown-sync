# Notion API: Complete Page Property Types Reference

> Source: Notion API docs (API version `2026-03-11`), fetched 2026-03-13

---

## Table of Contents

1. [Overview](#overview)
2. [PATCH /v1/pages/:id Request Format](#patch-request-format)
3. [POST /v1/pages Request Format](#post-request-format)
4. [Writable Property Types](#writable-property-types)
5. [Read-Only Property Types](#read-only-property-types)
6. [Unsupported / UI-Only Property Types](#unsupported-property-types)
7. [Key Behaviors & Gotchas](#key-behaviors)

---

## Overview

The Notion API recognizes **23+ property types**. Of these:
- **14 are fully writable** via API (can be set on create and update)
- **6 are read-only** (computed or auto-set by Notion)
- **2+ are unsupported** by the public API (returned as `null`)

### Property type categories at a glance

| Category | Types |
|----------|-------|
| **Text** | `title`, `rich_text` |
| **Scalar** | `number`, `checkbox`, `url`, `email`, `phone_number` |
| **Selection** | `select`, `multi_select`, `status` |
| **Temporal** | `date` |
| **Relational** | `people`, `files`, `relation` |
| **Computed (read-only)** | `formula`, `rollup`, `created_time`, `created_by`, `last_edited_time`, `last_edited_by`, `unique_id`, `verification` |
| **Unsupported** | `button`, `place` (returned as `null`) |

---

## PATCH Request Format

**Endpoint:** `PATCH https://api.notion.com/v1/pages/{page_id}`

```json
{
  "properties": {
    "Property Name": {
      "<type>": <value>
    }
  },
  "icon": { ... } | null,
  "cover": { ... } | null,
  "in_trash": false,
  "is_locked": false
}
```

Additional top-level parameters:
- `in_trash` (boolean) -- move to or restore from trash (replaces `archived` in API version 2026-03-11)
- `is_locked` (boolean) -- lock page editing in UI (API updates still work)
- `erase_content` (boolean) -- delete all block children (destructive, irreversible via API)
- `template` (object) -- apply a template; mutually exclusive with `erase_content` children

**Notes:**
- A page's **parent cannot be changed** via PATCH (use the Move Page API instead).
- For database pages, property keys must match the parent database schema.
- For standalone pages (page parent), only `title` can be updated.
- Read-only properties are silently ignored.

---

## POST Request Format

**Endpoint:** `POST https://api.notion.com/v1/pages`

```json
{
  "parent": {
    "type": "database_id",
    "database_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  },
  "properties": {
    "Name": {
      "title": [{ "text": { "content": "Page Title" } }]
    }
  },
  "children": [ ... ],
  "icon": { ... },
  "cover": { ... }
}
```

### Parent types

| Parent type | Property support | Notes |
|-------------|-----------------|-------|
| `database_id` | Full schema properties | Must match database schema |
| `data_source_id` | Full schema properties | Similar to database_id |
| `page_id` | Title only | Creates a child page |
| `workspace` (+ `workspace: true`) | None | Public integrations only |

### Content options (mutually exclusive)

- `children`: array of block objects (max 100)
- `content`: array of block objects (max 100)
- `markdown`: string (use `\n` for newlines)
- `template`: object specifying template to apply

**Yes, you can set properties AND content in the same POST call:**

```json
{
  "parent": { "database_id": "..." },
  "properties": {
    "Name": { "title": [{ "text": { "content": "My Page" } }] },
    "Status": { "status": { "name": "In Progress" } }
  },
  "children": [
    {
      "type": "paragraph",
      "paragraph": {
        "rich_text": [{ "text": { "content": "First paragraph." } }]
      }
    }
  ]
}
```

Or with markdown instead of children:

```json
{
  "parent": { "database_id": "..." },
  "properties": { "Name": { "title": [{ "text": { "content": "My Page" } }] } },
  "markdown": "# Heading\n\nParagraph content here."
}
```

---

## Writable Property Types

### 1. `title`

The page name. Every database has exactly one title property (always has `id: "title"`). Standalone pages also have a title.

**READ (GET response):**
```json
{
  "Name": {
    "id": "title",
    "type": "title",
    "title": [
      {
        "type": "text",
        "text": { "content": "My Page Title", "link": null },
        "annotations": {
          "bold": false, "italic": false, "strikethrough": false,
          "underline": false, "code": false, "color": "default"
        },
        "plain_text": "My Page Title",
        "href": null
      }
    ]
  }
}
```

**WRITE (PATCH/POST body):**
```json
{
  "Name": {
    "title": [
      { "text": { "content": "New Title" } }
    ]
  }
}
```

**Notes:**
- Max 25 rich text objects returned inline; use the property item endpoint for more.
- The `type` field is optional when writing.

---

### 2. `rich_text`

Multi-segment formatted text.

**READ:**
```json
{
  "Description": {
    "id": "HbZT",
    "type": "rich_text",
    "rich_text": [
      {
        "type": "text",
        "text": { "content": "Some formatted text", "link": null },
        "annotations": {
          "bold": false, "italic": false, "strikethrough": false,
          "underline": false, "code": false, "color": "default"
        },
        "plain_text": "Some formatted text",
        "href": null
      }
    ]
  }
}
```

**WRITE:**
```json
{
  "Description": {
    "rich_text": [
      { "text": { "content": "Updated text" } }
    ]
  }
}
```

**Notes:**
- Max 25 rich text objects inline; paginate via property item endpoint.
- Annotations (bold, italic, etc.) can be set on write.
- Supports `text`, `mention`, and `equation` rich text object types.

---

### 3. `number`

Numeric value with configurable format.

**READ:**
```json
{
  "Price": {
    "id": "WPj%5E",
    "type": "number",
    "number": 42.5
  }
}
```

**WRITE:**
```json
{
  "Price": {
    "number": 42.5
  }
}
```

**Clear:** `"number": null`

---

### 4. `select`

Single option from a predefined set.

**READ:**
```json
{
  "Priority": {
    "id": "Yc%3FJ",
    "type": "select",
    "select": {
      "id": "ou@_",
      "name": "High",
      "color": "red"
    }
  }
}
```

**WRITE (by name -- preferred):**
```json
{
  "Priority": {
    "select": { "name": "High" }
  }
}
```

**WRITE (by id):**
```json
{
  "Priority": {
    "select": { "id": "ou@_" }
  }
}
```

**Clear:** `"select": null`

**Notes:**
- Colors: `default`, `gray`, `brown`, `orange`, `yellow`, `green`, `blue`, `purple`, `pink`, `red`
- Colors are immutable via API (set in Notion UI).
- If the option name doesn't exist and the integration has write access, it will be auto-created.
- Commas are not allowed in option names.

---

### 5. `multi_select`

Multiple options from a predefined set.

**READ:**
```json
{
  "Tags": {
    "id": "QyRn",
    "type": "multi_select",
    "multi_select": [
      { "id": "tC;=", "name": "TypeScript", "color": "purple" },
      { "id": "e441...", "name": "JavaScript", "color": "red" }
    ]
  }
}
```

**WRITE:**
```json
{
  "Tags": {
    "multi_select": [
      { "name": "TypeScript" },
      { "name": "JavaScript" }
    ]
  }
}
```

**Clear:** `"multi_select": []`

**Notes:**
- Max 100 items per array.
- Replaces the entire array on update (not additive).
- New option names are auto-created if integration has write access.
- Commas not allowed in option names.

---

### 6. `status`

Status option (similar to select but with grouped states).

**READ:**
```json
{
  "Status": {
    "id": "Z%3ClH",
    "type": "status",
    "status": {
      "id": "539f2705-...",
      "name": "In progress",
      "color": "blue"
    }
  }
}
```

**WRITE (by name -- preferred):**
```json
{
  "Status": {
    "status": { "name": "Done" }
  }
}
```

**WRITE (by id):**
```json
{
  "Status": {
    "status": { "id": "539f2705-..." }
  }
}
```

**Clear:** `"status": null`

**Notes:**
- Status options and groups are managed in Notion UI only; the API cannot create/modify options.
- Database schema includes `options` array and `groups` array (each group has `option_ids`).

---

### 7. `date`

Date or date range with optional timezone.

**READ:**
```json
{
  "Due date": {
    "id": "M%3BBw",
    "type": "date",
    "date": {
      "start": "2023-02-07",
      "end": null,
      "time_zone": null
    }
  }
}
```

**WRITE (date only):**
```json
{
  "Due date": {
    "date": {
      "start": "2024-12-31"
    }
  }
}
```

**WRITE (date range with time and timezone):**
```json
{
  "Due date": {
    "date": {
      "start": "2024-01-01T09:00:00",
      "end": "2024-12-31T17:00:00",
      "time_zone": "America/New_York"
    }
  }
}
```

**Clear:** `"date": null`

**Notes:**
- `start` is required; `end` and `time_zone` are optional.
- Date formats: `YYYY-MM-DD` (date only) or `YYYY-MM-DDTHH:MM:SS` (with time).
- `time_zone` uses IANA timezone names (e.g., `America/New_York`, `Europe/London`).

---

### 8. `people`

Array of user references.

**READ:**
```json
{
  "Assignee": {
    "id": "%7BLUX",
    "type": "people",
    "people": [
      {
        "object": "user",
        "id": "c2f20311-...",
        "name": "Jane Doe",
        "avatar_url": null,
        "type": "person",
        "person": { "email": "jane@example.com" }
      }
    ]
  }
}
```

**WRITE:**
```json
{
  "Assignee": {
    "people": [
      { "object": "user", "id": "c2f20311-..." }
    ]
  }
}
```

**Clear:** `"people": []`

**Notes:**
- Max 25 people returned inline; use property item endpoint for full list.
- Also accepts groups: `{ "object": "group", "id": "group-id-..." }`.
- Replaces entire array on update.

---

### 9. `files`

Array of file references (external URLs or Notion-hosted uploads).

**READ:**
```json
{
  "Attachments": {
    "id": "tJPS",
    "type": "files",
    "files": [
      {
        "name": "Document",
        "type": "external",
        "external": { "url": "https://example.com/doc.pdf" }
      },
      {
        "name": "Upload",
        "type": "file",
        "file": {
          "url": "https://prod-files-secure.s3...",
          "expiry_time": "2024-12-03T19:44:56.932Z"
        }
      }
    ]
  }
}
```

**WRITE (external file):**
```json
{
  "Attachments": {
    "files": [
      {
        "type": "external",
        "name": "document.pdf",
        "external": { "url": "https://example.com/doc.pdf" }
      }
    ]
  }
}
```

**WRITE (file upload -- requires prior upload via File Upload API):**
```json
{
  "Attachments": {
    "files": [
      {
        "type": "file_upload",
        "name": "uploaded.pdf",
        "file_upload": { "id": "file-upload-id-123" }
      }
    ]
  }
}
```

**Clear:** `"files": []`

**Notes:**
- Replaces entire array on update (not additive).
- Notion-hosted file URLs expire (check `expiry_time`).

---

### 10. `checkbox`

Boolean value.

**READ:**
```json
{
  "Completed": {
    "id": "ZI%40W",
    "type": "checkbox",
    "checkbox": true
  }
}
```

**WRITE:**
```json
{
  "Completed": {
    "checkbox": true
  }
}
```

**Notes:** Cannot be set to `null`; use `false` to uncheck.

---

### 11. `url`

URL string.

**READ:**
```json
{
  "Website": {
    "id": "bB%3D%5B",
    "type": "url",
    "url": "https://developers.notion.com/"
  }
}
```

**WRITE:**
```json
{
  "Website": {
    "url": "https://example.com"
  }
}
```

**Clear:** `"url": null`

---

### 12. `email`

Email string.

**READ:**
```json
{
  "Contact": {
    "id": "y%5C%5E_",
    "type": "email",
    "email": "user@example.com"
  }
}
```

**WRITE:**
```json
{
  "Contact": {
    "email": "user@example.com"
  }
}
```

**Clear:** `"email": null`

---

### 13. `phone_number`

Phone number string (no format validation).

**READ:**
```json
{
  "Phone": {
    "id": "%5DKhQ",
    "type": "phone_number",
    "phone_number": "+1-555-0123"
  }
}
```

**WRITE:**
```json
{
  "Phone": {
    "phone_number": "+1-555-0123"
  }
}
```

**Clear:** `"phone_number": null`

---

### 14. `relation`

Array of related page references.

**READ:**
```json
{
  "Related Tasks": {
    "id": "hgMz",
    "type": "relation",
    "relation": [
      { "id": "dd456007-6c66-4bba-957e-ea501dcda3a6" },
      { "id": "0c1f7cb2-8090-4f18-924e-d92965055e32" }
    ],
    "has_more": false
  }
}
```

**WRITE:**
```json
{
  "Related Tasks": {
    "relation": [
      { "id": "dd456007-6c66-4bba-957e-ea501dcda3a6" },
      { "id": "0c1f7cb2-8090-4f18-924e-d92965055e32" }
    ]
  }
}
```

**Clear:** `"relation": []`

**Notes:**
- Max 25 relations returned inline; check `has_more` flag.
- If `has_more: true`, use the property item endpoint to paginate: `GET /v1/pages/{page_id}/properties/{property_id}`.
- The related database must be shared with the integration.
- Replaces entire array on update.
- Database schema includes `data_source_id` (or `database_id`), `synced_property_id`, and `synced_property_name` for the reciprocal relation.

---

## Read-Only Property Types

These are computed or auto-set by Notion. They appear in GET responses but **cannot be set or modified** via PATCH/POST. The API silently ignores them if included in a write request.

### 15. `formula`

Computed value from a formula expression.

**READ:**
```json
{
  "Days until launch": {
    "id": "CSoE",
    "type": "formula",
    "formula": {
      "type": "number",
      "number": 56
    }
  }
}
```

**Formula subtypes:**

| Subtype | Example value |
|---------|--------------|
| `string` | `{ "type": "string", "string": "hello" }` |
| `number` | `{ "type": "number", "number": 42 }` |
| `boolean` | `{ "type": "boolean", "boolean": true }` |
| `date` | `{ "type": "date", "date": { "start": "2024-01-01", "end": null, "time_zone": null } }` |

**Notes:**
- Max 25 inline references; use property item endpoint for complete data.
- The formula expression is defined in the database schema: `"formula": { "expression": "prop(\"Price\") * 1.1" }`.

---

### 16. `rollup`

Aggregated value computed from a relation's properties.

**READ:**
```json
{
  "Total Items": {
    "id": "hgMz",
    "type": "rollup",
    "rollup": {
      "type": "number",
      "number": 15,
      "function": "sum"
    }
  }
}
```

**Rollup subtypes:**

| Subtype | Example value |
|---------|--------------|
| `number` | `{ "type": "number", "number": 15, "function": "sum" }` |
| `date` | `{ "type": "date", "date": { "start": "2024-01-01", "end": null, "time_zone": null }, "function": "earliest_date" }` |
| `array` | `{ "type": "array", "array": [ ... property value objects ... ], "function": "show_original" }` |
| `incomplete` | `{ "type": "incomplete", "incomplete": {}, "function": "..." }` |
| `unsupported` | `{ "type": "unsupported", "unsupported": {}, "function": "..." }` |

**Rollup functions:** `average`, `checked`, `count`, `count_per_group`, `count_values`, `date_range`, `earliest_date`, `empty`, `latest_date`, `max`, `median`, `min`, `not_empty`, `percent_checked`, `percent_empty`, `percent_not_empty`, `percent_per_group`, `percent_unchecked`, `range`, `show_original`, `show_unique`, `sum`, `unchecked`, `unique`

**Notes:**
- The `array` subtype (from `show_original` or `show_unique`) contains nested property value objects.
- Use property item endpoint for >25 referenced items.
- Database schema: `"rollup": { "function": "sum", "relation_property_id": "...", "relation_property_name": "...", "rollup_property_id": "...", "rollup_property_name": "..." }`

---

### 17. `created_time`

Auto-set page creation timestamp.

**READ:**
```json
{
  "Created": {
    "id": "eB_%7D",
    "type": "created_time",
    "created_time": "2022-10-24T22:54:00.000Z"
  }
}
```

---

### 18. `created_by`

Auto-set page creator.

**READ:**
```json
{
  "Creator": {
    "id": "...",
    "type": "created_by",
    "created_by": {
      "object": "user",
      "id": "c2f20311-..."
    }
  }
}
```

---

### 19. `last_edited_time`

Auto-updated page modification timestamp.

**READ:**
```json
{
  "Modified": {
    "id": "%3Defk",
    "type": "last_edited_time",
    "last_edited_time": "2023-02-24T21:06:00.000Z"
  }
}
```

---

### 20. `last_edited_by`

Auto-updated last editor.

**READ:**
```json
{
  "Editor": {
    "id": "uGNN",
    "type": "last_edited_by",
    "last_edited_by": {
      "object": "user",
      "id": "9188c6a5-...",
      "name": "Test Integration",
      "type": "bot",
      "bot": {}
    }
  }
}
```

---

### 21. `unique_id`

Auto-incrementing ID with optional prefix.

**READ:**
```json
{
  "ID": {
    "id": "tqqd",
    "type": "unique_id",
    "unique_id": {
      "number": 3,
      "prefix": "TASK"
    }
  }
}
```

**Notes:**
- `prefix` is `null` if not configured.
- Cannot be set or modified via API.
- Database schema: `"unique_id": { "prefix": "TASK" }`

---

### 22. `verification`

Wiki verification state (wiki databases only).

**READ (unverified):**
```json
{
  "Verification": {
    "id": "fpVq",
    "type": "verification",
    "verification": {
      "state": "unverified",
      "verified_by": null,
      "date": null
    }
  }
}
```

**READ (verified):**
```json
{
  "Verification": {
    "id": "fpVq",
    "type": "verification",
    "verification": {
      "state": "verified",
      "verified_by": {
        "object": "user",
        "id": "01e46064-...",
        "name": "User Name",
        "type": "person",
        "person": {}
      },
      "date": {
        "start": "2023-08-01T04:00:00.000Z",
        "end": null,
        "time_zone": null
      }
    }
  }
}
```

**Notes:**
- Only present on wiki database pages.
- `state`: `"verified"` or `"unverified"`.
- Cannot be set via public API.

---

## Unsupported Property Types

These exist in the Notion UI but are **not supported by the public API**. They are returned with `null` values in GET responses. Exclude them from write requests.

### 23. `button`

**READ:**
```json
{
  "Run Action": {
    "id": "...",
    "type": "button",
    "button": {}
  }
}
```

Not readable or writable via API. Returns empty object.

---

### 24. `place`

Location field (available in Notion UI with map view).

**READ:**
```json
{
  "Location": {
    "id": "%60%40Gq",
    "type": "place",
    "place": null
  }
}
```

**Notes:**
- The PATCH page endpoint documentation shows a write structure with `lat`, `lon`, `name`, `address`, `aws_place_id`, `google_place_id` -- but the page property values docs list this as unsupported (returns `null`).
- Treat as unsupported/experimental. If write support exists, the structure would be:

```json
{
  "Location": {
    "place": {
      "lat": 40.7128,
      "lon": -74.0060,
      "name": "New York City",
      "address": "New York, NY, USA"
    }
  }
}
```

---

## Key Behaviors

### Database pages vs standalone pages

| Behavior | Database page | Standalone page (page parent) |
|----------|--------------|-------------------------------|
| Writable properties | All writable types matching schema | Title only |
| Property schema | Must match parent database | N/A |
| Content (children) | Yes | Yes |
| Markdown content | Yes | Yes |

### Pagination for property values

Several property types return at most **25 items inline** in the GET /v1/pages/:id response. For full data, use the property item endpoint:

```
GET /v1/pages/{page_id}/properties/{property_id}
```

Types requiring pagination:
- `title` (>25 rich text segments)
- `rich_text` (>25 rich text segments)
- `relation` (>25 related pages -- check `has_more` flag)
- `people` (>25 people)
- `formula` (when referencing >25 items)
- `rollup` (when array contains >25 items)

### Clearing/nulling property values

| Type | How to clear |
|------|-------------|
| `number` | `null` |
| `select` | `null` |
| `status` | `null` |
| `date` | `null` |
| `url` | `null` |
| `email` | `null` |
| `phone_number` | `null` |
| `checkbox` | `false` (cannot be null) |
| `multi_select` | `[]` (empty array) |
| `people` | `[]` (empty array) |
| `files` | `[]` (empty array) |
| `relation` | `[]` (empty array) |
| `title` | Cannot be cleared (always required) |
| `rich_text` | `[]` (empty array) |

### Array properties replace entirely on update

When you update `multi_select`, `people`, `files`, or `relation`, the entire array is **replaced**, not merged. To add an item, you must include all existing items plus the new one.

### Auto-created options

For `select` and `multi_select`, if you write an option `name` that doesn't exist in the database schema and the integration has write access, **Notion auto-creates the option**.

This does NOT apply to `status` -- status options must be pre-configured in the Notion UI.

### The `type` field is optional when writing

When writing properties, you can omit the `type` field. These are equivalent:

```json
{ "Priority": { "type": "select", "select": { "name": "High" } } }
{ "Priority": { "select": { "name": "High" } } }
```

### Icon and cover (top-level, not properties)

Icon and cover are **not** inside the `properties` object. They are top-level fields:

```json
{
  "icon": { "type": "emoji", "emoji": "🎯" },
  "cover": { "type": "external", "external": { "url": "https://..." } }
}
```

Clear with: `"icon": null` or `"cover": null`

Icon types: `emoji`, `external`, `file`, `file_upload`, `custom_emoji`
Cover types: `external`, `file_upload`

### API version 2026-03-11 breaking changes

- `in_trash` replaces `archived` in all request/response bodies.
- `position` object replaces the flat `after` string parameter for block placement.
- `meeting_notes` replaces `transcription` block type.

### Max array limits

- `multi_select`: 100 items
- `children` / `content` blocks in POST: 100 items
- Rich text arrays: 100 segments per property
