#!/usr/bin/env python3
"""
GFM-to-Notion Markdown Preprocessor (auto-detecting)

Automatically detects whether a markdown file is standard GFM or already in
Notion's enhanced format, and only converts when needed. Safe to run on any
markdown file — Notion-format content passes through unchanged.

Usage:
  python notion_preprocess.py <input_file> [--output <output_file>] [--in-place]

If --output is omitted and --in-place is not set, prints to stdout.
"""

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

# Tags/patterns that only appear in Notion's enhanced markdown
NOTION_MARKERS = [
    "<table",
    "<callout",
    "<details",
    "<columns",
    "<empty-block",
    "<synced_block",
    "<mention-",
    '<span color=',
    '<span underline=',
    "{color=",
    '{toggle="true"',
]


def is_notion_format(content: str) -> bool:
    """Return True if content is already in Notion's enhanced markdown format.

    Checks for Notion-only tags outside code blocks. A single match is enough
    — standard GFM never contains these patterns.
    """
    in_code = False
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for marker in NOTION_MARKERS:
            if marker in line:
                return True
    return False


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------


def is_table_separator(line: str) -> bool:
    """Check if a line is a GFM table separator like |---|---|"""
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return False
    cells = stripped.strip("|").split("|")
    return all(re.match(r"\s*:?-{1,}:?\s*$", c) for c in cells)


def parse_table_cells(line: str) -> list[str]:
    """Parse a GFM table row into cell contents."""
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [c.strip() for c in stripped.split("|")]


def convert_pipe_table(lines: list[str]) -> list[str]:
    """Convert GFM pipe table lines to Notion <table> HTML format."""
    if len(lines) < 2:
        return lines

    has_header = len(lines) >= 2 and is_table_separator(lines[1])

    data_rows = []
    if has_header:
        data_rows.append(parse_table_cells(lines[0]))
        data_rows.extend(parse_table_cells(l) for l in lines[2:])
    else:
        data_rows.extend(parse_table_cells(l) for l in lines)

    header_attr = ' header-row="true"' if has_header else ""
    result = [f"<table{header_attr}>"]
    for row in data_rows:
        result.append("<tr>")
        for cell in row:
            result.append(f"<td>{process_inline(cell)}</td>")
        result.append("</tr>")
    result.append("</table>")
    return result


# ---------------------------------------------------------------------------
# Inline transforms (only applied outside code blocks and code spans)
# ---------------------------------------------------------------------------


def _split_code_spans(text: str) -> list[str]:
    """Split text into alternating [non-code, code, non-code, ...] parts."""
    return re.split(r"(`[^`]+`|\[[^\]]*\]\([^)]*\))", text)


def _is_protected(part: str) -> bool:
    """True if part is an inline code span or markdown link (skip transforms)."""
    return (part.startswith("`") and part.endswith("`")) or (
        part.startswith("[") and "(" in part
    )


def process_arrows(text: str) -> str:
    """Replace arrow sequences with Unicode arrows outside code spans."""
    parts = _split_code_spans(text)
    for i, part in enumerate(parts):
        if _is_protected(part):
            continue
        # Order matters: longer patterns first
        part = re.sub(r"<=>", "⇔", part)
        part = re.sub(r"<->", "↔", part)
        part = re.sub(r"<--", "←", part)
        part = re.sub(r"-->", "→", part)
        part = re.sub(r"=>", "⇒", part)
        part = re.sub(r"<-", "←", part)
        part = re.sub(r"->", "→", part)
        parts[i] = part
    return "".join(parts)


def process_dashes(text: str) -> str:
    """Replace standalone -- with em dash. Skip --flag and ---."""
    parts = _split_code_spans(text)
    for i, part in enumerate(parts):
        if _is_protected(part):
            continue
        part = re.sub(r"(?<!-)--(?![-\w])", "—", part)
        parts[i] = part
    return "".join(parts)


def escape_tildes(text: str) -> str:
    """Escape standalone ~ to prevent Notion strikethrough interpretation.
    Skips ~~strikethrough~~."""
    parts = _split_code_spans(text)
    for i, part in enumerate(parts):
        if _is_protected(part):
            continue
        part = re.sub(r"(?<!~)~(?!~)", r"\\~", part)
        parts[i] = part
    return "".join(parts)


def escape_autolinks(text: str) -> str:
    """Wrap bare filenames (file.sh) in backticks to prevent Notion auto-linking."""
    parts = _split_code_spans(text)
    for i, part in enumerate(parts):
        if _is_protected(part):
            continue
        part = re.sub(
            r"(?<![/.])(?<!\w)(\w[\w-]+)\.(sh|js|py|ts|go|rs|rb|yml|yaml|json|toml|env|md|txt|css|html|xml)\b",
            r"`\1.\2`",
            part,
        )
        parts[i] = part
    return "".join(parts)


def process_inline(text: str) -> str:
    """Apply all inline transforms."""
    text = process_arrows(text)
    text = process_dashes(text)
    text = escape_tildes(text)
    text = escape_autolinks(text)
    return text


# ---------------------------------------------------------------------------
# GFM callout map
# ---------------------------------------------------------------------------

GFM_CALLOUT_MAP = {
    "NOTE": ("ℹ️", "blue_bg"),
    "TIP": ("💡", "green_bg"),
    "IMPORTANT": ("❗", "purple_bg"),
    "WARNING": ("⚠️", "yellow_bg"),
    "CAUTION": ("🔴", "red_bg"),
}


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def preprocess(content: str) -> str:
    """Auto-detecting preprocessor: converts GFM → Notion, skips Notion format.

    Safe to call on any markdown file. If the content already contains Notion-
    specific tags (<table>, <callout>, {color=}, etc.), it is returned unchanged.
    """
    if is_notion_format(content):
        return content

    lines = content.split("\n")
    output: list[str] = []
    i = 0
    in_code_block = False
    code_fence = ""

    while i < len(lines):
        line = lines[i]

        # Track fenced code blocks
        fence_match = re.match(r"^(\s*)(```|~~~)([\w ]*)\s*$", line)
        if fence_match:
            indent = fence_match.group(1)
            fence = fence_match.group(2)
            lang = fence_match.group(3).strip()

            if not in_code_block:
                in_code_block = True
                code_fence = fence
                if not lang:
                    output.append(f"{indent}{fence}plain text")
                else:
                    output.append(line)
                i += 1
                continue
            elif fence == code_fence:
                in_code_block = False
                code_fence = ""
                output.append(line)
                i += 1
                continue

        # Inside code block — pass through unchanged
        if in_code_block:
            output.append(line)
            i += 1
            continue

        # GFM callout syntax: > [!NOTE], > [!TIP], etc.
        callout_match = re.match(
            r"^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$", line
        )
        if callout_match:
            kind = callout_match.group(1)
            icon, color = GFM_CALLOUT_MAP[kind]
            body_lines = []
            j = i + 1
            while j < len(lines) and re.match(r"^>", lines[j]):
                body_text = re.sub(r"^>\s?", "", lines[j])
                body_lines.append(f"\t{body_text}" if body_text else "")
                j += 1
            output.append(f'<callout icon="{icon}" color="{color}">')
            output.extend(body_lines)
            output.append("</callout>")
            i = j
            continue

        # GFM pipe table detection
        if re.match(r"^\s*\|.+\|", line):
            table_lines = [line]
            j = i + 1
            while j < len(lines) and re.match(r"^\s*\|.+\|", lines[j]):
                table_lines.append(lines[j])
                j += 1
            if len(table_lines) >= 2 and (
                is_table_separator(table_lines[1])
                or len(table_lines) >= 3
            ):
                converted = convert_pipe_table(table_lines)
                output.extend(converted)
                i = j
                continue

        # Multi-line blockquotes → single > with <br>
        if re.match(r"^>\s", line) and not re.match(r"^>\s*\[!", line):
            quote_lines = []
            j = i
            while j < len(lines) and re.match(r"^>", lines[j]):
                text = re.sub(r"^>\s?", "", lines[j])
                quote_lines.append(text)
                j += 1
            if len(quote_lines) > 1:
                joined = "<br>".join(quote_lines)
                output.append(f"> {process_inline(joined)}")
                i = j
                continue

        # Regular line — apply inline transformations
        output.append(process_inline(line))
        i += 1

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Auto-detecting GFM-to-Notion markdown preprocessor"
    )
    parser.add_argument("input_file", help="Input markdown file")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument(
        "--in-place",
        "-i",
        action="store_true",
        help="Modify the input file in place",
    )
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    content = input_path.read_text(encoding="utf-8")

    if is_notion_format(content):
        print("Notion format detected — skipping preprocessing", file=sys.stderr)
        result = content
    else:
        print("GFM format detected — preprocessing", file=sys.stderr)
        result = preprocess(content)

    if args.in_place:
        input_path.write_text(result, encoding="utf-8")
    elif args.output:
        Path(args.output).write_text(result, encoding="utf-8")
    else:
        print(result)


if __name__ == "__main__":
    main()
