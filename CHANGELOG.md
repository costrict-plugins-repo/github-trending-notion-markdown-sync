# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-03-14

### Added
- Push local markdown files to Notion (new pages + updates)
- Pull Notion pages to local markdown with YAML frontmatter
- Two-way sync with conflict detection
- Auto-detecting GFM preprocessor (tables, arrows, dashes, tildes, callouts, autolinks)
- Media download on pull (pre-signed S3 URLs to local assets)
- Media upload on push (local files via File Upload API)
- Database page properties in YAML frontmatter (select, multi-select, date, people, relations, etc.)
- Page icon replication (emoji, external URLs, custom emoji)
- Notion compatibility validation
- H1/title handling for both standalone and database pages
- Truncation handling for large pages (20,000+ blocks)
- Plugin manifest and marketplace configuration
- Privacy policy
- 5 eval scenarios with 34 assertions
