#!/usr/bin/env python3
"""Notion media handler for the notion-markdown-sync plugin.

Downloads media from pulled Notion pages (pre-signed S3 URLs → local assets)
and uploads local media before pushing (local paths → Notion-hosted URLs).

Usage:
  Download (after pull):
    python notion_media.py download <markdown-file> [--assets-dir DIR]

  Upload (before push):
    python notion_media.py upload <markdown-file> --page-id PAGE_ID

Requires NOTION_API_KEY environment variable.
"""

import os
import sys
import re
import json
import hashlib
import mimetypes
import urllib.request
import urllib.parse
from urllib.error import HTTPError

API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2026-03-11"

# Pre-signed URL detection patterns
S3_PATTERNS = [
    re.compile(r"prod-files-secure\.s3\.us-west-2\.amazonaws\.com"),
    re.compile(r"s3\.us-west-2\.amazonaws\.com/secure\.notion-static\.com"),
]


def get_api_key():
    key = os.environ.get("NOTION_API_KEY", "")
    if not key:
        print("Error: NOTION_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    return key


def api_headers():
    return {
        "Authorization": f"Bearer {get_api_key()}",
        "Notion-Version": NOTION_VERSION,
    }


def api_request(method, path, data=None):
    """Make a JSON Notion API request."""
    headers = api_headers()
    headers["Content-Type"] = "application/json"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        f"{API_BASE}{path}", data=body, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        err_body = e.read().decode()
        print(f"API error {e.code} on {method} {path}: {err_body}", file=sys.stderr)
        raise


def is_notion_presigned(url):
    """Check if a URL is a Notion pre-signed S3 URL."""
    return any(p.search(url) for p in S3_PATTERNS) and "X-Amz-Algorithm" in url


def extract_filename(url):
    """Extract a clean filename from a pre-signed URL."""
    parsed = urllib.parse.urlparse(url)
    path = urllib.parse.unquote(parsed.path)
    name = path.split("/")[-1]
    return name or "unknown"


def find_presigned_urls(content):
    """Find all Notion pre-signed media URLs in markdown.

    Returns list of (full_match, url, media_type).
    """
    results = []

    # Images: ![caption](url) or ![caption](url) {color="..."}
    for m in re.finditer(r"(!\[[^\]]*\]\(([^)\s]+)\))", content):
        url = m.group(2)
        if is_notion_presigned(url):
            results.append((m.group(1), url, "image"))

    # Media tags: <audio src="url">...</audio>, <video>, <file>, <pdf>
    for m in re.finditer(
        r'(<(audio|video|file|pdf)\s+src="([^"]+)"[^>]*>(?:[^<]*)</\2>)', content
    ):
        url = m.group(3)
        if is_notion_presigned(url):
            results.append((m.group(1), url, m.group(2)))

    # Self-closing media tags: <audio src="url"/>
    for m in re.finditer(
        r'(<(audio|video|file|pdf)\s+src="([^"]+)"[^/]*/\s*>)', content
    ):
        url = m.group(3)
        if is_notion_presigned(url) and (m.group(1), url, m.group(2)) not in results:
            results.append((m.group(1), url, m.group(2)))

    return results


def find_local_media(content, base_dir):
    """Find all local media paths in markdown.

    Returns list of (full_match, local_path, media_type).
    """
    results = []

    # Images: ![caption](local/path)
    for m in re.finditer(r"(!\[[^\]]*\]\(([^)\s]+)\))", content):
        path = m.group(2)
        if not path.startswith(("http://", "https://", "#", "data:")):
            full = os.path.join(base_dir, path)
            if os.path.isfile(full):
                results.append((m.group(1), path, "image"))

    # Media tags with local paths
    for m in re.finditer(
        r'(<(audio|video|file|pdf)\s+src="([^"]+)"([^>]*)>([^<]*)</\2>)', content
    ):
        path = m.group(3)
        if not path.startswith(("http://", "https://")):
            full = os.path.join(base_dir, path)
            if os.path.isfile(full):
                results.append((m.group(1), path, m.group(2)))

    return results


def download_file(url, dest_path):
    """Download a URL to a local path."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=60) as resp:
        with open(dest_path, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)


def upload_file(file_path):
    """Upload a local file via Notion File Upload API.

    Returns the file_upload ID.
    """
    filename = os.path.basename(file_path)
    content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    file_size = os.path.getsize(file_path)

    # Step 1: Create the upload
    result = api_request(
        "POST",
        "/file_uploads",
        {
            "mode": "single_part",
            "filename": filename,
            "content_type": content_type,
        },
    )
    upload_id = result["id"]

    # Step 2: Send file data via multipart/form-data
    boundary = f"----NotionUpload{hashlib.md5(file_path.encode()).hexdigest()}"
    with open(file_path, "rb") as f:
        file_data = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n"
        f"\r\n"
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()

    headers = api_headers()
    headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"

    req = urllib.request.Request(
        f"{API_BASE}/file_uploads/{upload_id}/send",
        data=body,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        json.loads(resp.read())

    return upload_id


def block_type_for(media_type):
    """Map media_type string to Notion block type."""
    mapping = {
        "image": "image",
        "audio": "audio",
        "video": "video",
        "file": "file",
        "pdf": "file",
    }
    return mapping.get(media_type, "file")


def append_media_block(page_id, upload_id, media_type, caption=""):
    """Append a temporary media block to a page using a file_upload reference.

    Returns the created block ID.
    """
    bt = block_type_for(media_type)
    block = {
        "type": bt,
        bt: {
            "type": "file_upload",
            "file_upload": {"id": upload_id},
        },
    }
    if caption:
        block[bt]["caption"] = [{"type": "text", "text": {"content": caption}}]

    result = api_request(
        "PATCH", f"/blocks/{page_id}/children", {"children": [block]}
    )
    return result["results"][0]["id"]


def delete_block(block_id):
    """Delete a block by ID."""
    try:
        api_request("DELETE", f"/blocks/{block_id}")
    except Exception:
        pass  # Best-effort cleanup


def get_page_markdown(page_id):
    """GET /v1/pages/:id/markdown"""
    headers = api_headers()
    req = urllib.request.Request(
        f"{API_BASE}/pages/{page_id}/markdown", headers=headers
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


# ── Download command ──────────────────────────────────────────────────────────


def cmd_download(md_file, assets_dir="assets"):
    """Download pre-signed media from a pulled markdown file to local assets."""
    with open(md_file, "r") as f:
        content = f.read()

    base_dir = os.path.dirname(os.path.abspath(md_file))
    full_assets = os.path.join(base_dir, assets_dir)

    media = find_presigned_urls(content)
    if not media:
        print("No pre-signed media URLs found.")
        return

    print(f"Found {len(media)} media file(s) to download...")
    downloaded = 0
    for full_match, url, media_type in media:
        filename = extract_filename(url)

        # Avoid overwriting — add hash suffix if file exists with same name
        dest = os.path.join(full_assets, filename)
        if os.path.exists(dest):
            h = hashlib.md5(url.encode()).hexdigest()[:8]
            name, ext = os.path.splitext(filename)
            filename = f"{name}-{h}{ext}"
            dest = os.path.join(full_assets, filename)

        print(f"  [{media_type}] {filename}")
        try:
            download_file(url, dest)
        except Exception as e:
            print(f"  WARNING: Failed to download {filename}: {e}", file=sys.stderr)
            continue

        # Rewrite the URL to a local relative path
        local_path = f"{assets_dir}/{filename}"
        if media_type == "image":
            new_match = re.sub(r"\([^)\s]+\)", f"({local_path})", full_match)
        else:
            new_match = full_match.replace(f'src="{url}"', f'src="{local_path}"')
        content = content.replace(full_match, new_match)
        downloaded += 1

    with open(md_file, "w") as f:
        f.write(content)

    print(f"Done. {downloaded}/{len(media)} files saved to {assets_dir}/")


# ── Upload command ────────────────────────────────────────────────────────────


def cmd_upload(md_file, page_id):
    """Upload local media referenced in markdown to Notion, replacing paths with Notion URLs.

    Strategy (required because the markdown API only accepts URLs, not file_upload IDs):
    1. Upload each local file via File Upload API
    2. Append temporary media blocks to the page via blocks API (using file_upload refs)
    3. GET page markdown — now contains Notion-hosted URLs for the uploaded files
    4. Match filenames in those URLs to build a local-path → Notion-URL mapping
    5. Delete the temporary blocks
    6. Rewrite local paths in the markdown with the resolved Notion URLs
    """
    with open(md_file, "r") as f:
        content = f.read()

    base_dir = os.path.dirname(os.path.abspath(md_file))
    media = find_local_media(content, base_dir)

    if not media:
        print("No local media files found.")
        return

    print(f"Found {len(media)} local media file(s) to upload...")

    # Upload files and create temporary blocks
    temp_blocks = []  # (block_id, filename, full_match, local_path, media_type)
    for full_match, local_path, media_type in media:
        abs_path = os.path.join(base_dir, local_path)
        filename = os.path.basename(local_path)

        print(f"  Uploading [{media_type}] {filename}")
        try:
            upload_id = upload_file(abs_path)
            block_id = append_media_block(page_id, upload_id, media_type)
            temp_blocks.append((block_id, filename, full_match, local_path, media_type))
        except Exception as e:
            print(
                f"  WARNING: Failed to upload {filename}: {e}", file=sys.stderr
            )
            continue

    if not temp_blocks:
        print("No files uploaded successfully.")
        return

    # GET page markdown to resolve Notion-hosted URLs
    print("  Resolving Notion-hosted URLs...")
    page_md = get_page_markdown(page_id)
    notion_markdown = page_md.get("markdown", "")

    # Build local_path → Notion URL mapping by matching filenames
    url_map = {}
    for block_id, filename, full_match, local_path, media_type in temp_blocks:
        # Notion pre-signed URLs contain the original filename (URL-encoded)
        encoded_name = urllib.parse.quote(filename, safe="")
        # Try URL-encoded filename first, then raw
        for search_name in [encoded_name, filename]:
            pattern = r"(https://[^\s\)\">]+?" + re.escape(search_name) + r"[^\s\)\">]*)"
            m = re.search(pattern, notion_markdown)
            if m:
                url_map[local_path] = m.group(1)
                break
        else:
            print(
                f"  WARNING: Could not resolve Notion URL for {filename}",
                file=sys.stderr,
            )

    # Delete temporary blocks
    print("  Cleaning up temporary blocks...")
    for block_id, *_ in temp_blocks:
        delete_block(block_id)

    # Rewrite local paths with Notion URLs
    for full_match, local_path, media_type in media:
        if local_path in url_map:
            notion_url = url_map[local_path]
            if media_type == "image":
                new_match = full_match.replace(f"({local_path})", f"({notion_url})")
            else:
                new_match = full_match.replace(
                    f'src="{local_path}"', f'src="{notion_url}"'
                )
            content = content.replace(full_match, new_match)

    with open(md_file, "w") as f:
        f.write(content)

    print(f"Done. {len(url_map)}/{len(temp_blocks)} URLs resolved.")


# ── CLI ───────────────────────────────────────────────────────────────────────


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    md_file = sys.argv[2]

    if not os.path.isfile(md_file):
        print(f"Error: File not found: {md_file}", file=sys.stderr)
        sys.exit(1)

    if cmd == "download":
        assets_dir = "assets"
        if "--assets-dir" in sys.argv:
            idx = sys.argv.index("--assets-dir")
            if idx + 1 < len(sys.argv):
                assets_dir = sys.argv[idx + 1]
        cmd_download(md_file, assets_dir)

    elif cmd == "upload":
        page_id = None
        if "--page-id" in sys.argv:
            idx = sys.argv.index("--page-id")
            if idx + 1 < len(sys.argv):
                page_id = sys.argv[idx + 1]
        if not page_id:
            print("Error: --page-id required for upload", file=sys.stderr)
            sys.exit(1)
        cmd_upload(md_file, page_id)

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
