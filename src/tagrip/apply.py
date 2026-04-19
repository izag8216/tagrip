"""Frontmatter tag writer -- apply extracted tags to markdown files."""

from __future__ import annotations

import re
from pathlib import Path

from .parser import ParsedMarkdown, parse_markdown


def apply_tags(
    path: Path,
    tags: list[str],
    dry_run: bool = False,
    merge: bool = True,
) -> dict[str, list[str]]:
    """Apply tags to a markdown file's YAML frontmatter.

    Returns dict with 'added' and 'existing' tag lists.
    """
    parsed = parse_markdown(path)
    existing_tags = _get_existing_tags(parsed)
    existing_lower = {t.lower() for t in existing_tags}

    new_tags = [t for t in tags if t.lower() not in existing_lower]
    if merge:
        final_tags = existing_tags + new_tags
    else:
        final_tags = tags
        new_tags = [t for t in tags if t.lower() not in existing_lower]

    if dry_run:
        return {"added": new_tags, "existing": existing_tags}

    updated_text = _write_frontmatter_tags(parsed, final_tags)
    path.write_text(updated_text, encoding="utf-8")
    return {"added": new_tags, "existing": existing_tags}


def _get_existing_tags(parsed: ParsedMarkdown) -> list[str]:
    """Extract tags list from parsed frontmatter."""
    tags = parsed.frontmatter.get("tags", [])
    if isinstance(tags, str):
        return [t.strip() for t in tags.split(",") if t.strip()]
    if isinstance(tags, list):
        return [str(t).strip() for t in tags if str(t).strip()]
    return []


def _write_frontmatter_tags(parsed: ParsedMarkdown, tags: list[str]) -> str:
    """Rewrite the file with updated frontmatter tags."""
    if not parsed.has_frontmatter:
        fm_lines = ["---"]
        for key, value in parsed.frontmatter.items():
            if key != "tags":
                fm_lines.append(f"{key}: {value}")
        fm_lines.append("tags:")
        for tag in tags:
            fm_lines.append(f"  - {tag}")
        fm_lines.append("---")
        return "\n".join(fm_lines) + "\n" + parsed.body

    lines = parsed.raw_frontmatter.split("\n")
    out_lines: list[str] = []
    skip_tags = False
    for line in lines:
        if re.match(r"^tags:", line):
            skip_tags = True
            continue
        if skip_tags and re.match(r"^\s+-\s+", line):
            continue
        skip_tags = False
        out_lines.append(line)

    tag_block = "tags:"
    for tag in tags:
        tag_block += f"\n  - {tag}"
    out_lines.append(tag_block)

    return "---\n" + "\n".join(out_lines) + "\n---\n" + parsed.body
