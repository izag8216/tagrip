"""Markdown parser -- extract text content and YAML frontmatter."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ParsedMarkdown:
    frontmatter: dict[str, object]
    body: str
    raw_frontmatter: str
    has_frontmatter: bool
    path: Path


def _parse_yaml_simple(text: str) -> dict[str, object]:
    """Minimal YAML parser for frontmatter (no external dependency needed for basic cases)."""
    result: dict[str, object] = {}
    current_list_key: str | None = None
    current_list: list[str] = []

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if line.startswith("  - ") and current_list_key:
            current_list.append(stripped.lstrip("- ").strip().strip('"').strip("'"))
            continue

        if current_list_key and current_list:
            result[current_list_key] = current_list
            current_list = []
            current_list_key = None

        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if not value:
                current_list_key = key
                current_list = []
            else:
                result[key] = value

    if current_list_key and current_list:
        result[current_list_key] = current_list

    return result


def parse_markdown(path: Path) -> ParsedMarkdown:
    """Parse a markdown file into frontmatter dict and body text."""
    text = path.read_text(encoding="utf-8")
    return parse_markdown_text(text, path)


def parse_markdown_text(text: str, path: Path | None = None) -> ParsedMarkdown:
    """Parse markdown text into frontmatter dict and body text."""
    if path is None:
        path = Path("unknown.md")

    if not text.startswith("---"):
        return ParsedMarkdown(
            frontmatter={},
            body=text,
            raw_frontmatter="",
            has_frontmatter=False,
            path=path,
        )

    end_match = re.search(r"\n---\n", text[3:])
    if end_match is None:
        end_match = re.search(r"\n---\s*$", text[3:])
    if end_match is None:
        return ParsedMarkdown(
            frontmatter={},
            body=text,
            raw_frontmatter="",
            has_frontmatter=False,
            path=path,
        )

    raw_fm = text[3 : 3 + end_match.start()]
    body = text[3 + end_match.end() :]
    frontmatter = _parse_yaml_simple(raw_fm)

    return ParsedMarkdown(
        frontmatter=frontmatter,
        body=body,
        raw_frontmatter=raw_fm,
        has_frontmatter=True,
        path=path,
    )


def strip_markdown_syntax(text: str) -> str:
    """Remove markdown formatting to get plain text for analysis."""
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[[^\]]*\]\([^)]*\)", lambda m: m.group(0).split("](")[0][1:], text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_~]{1,3}([^*_~]+)[*_~]{1,3}", r"\1", text)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*>+\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\|", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_headings(body: str) -> list[str]:
    """Extract heading texts from markdown body."""
    headings: list[str] = []
    for match in re.finditer(r"^#{1,6}\s+(.+)$", body, re.MULTILINE):
        heading = match.group(1).strip()
        heading = re.sub(r"[*_~`]{1,3}", "", heading)
        headings.append(heading)
    return headings


def extract_wikilinks(body: str) -> list[str]:
    """Extract [[wikilink]] targets from markdown body."""
    return re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", body)


def extract_code_languages(body: str) -> list[str]:
    """Extract programming language identifiers from fenced code blocks."""
    return re.findall(r"```(\w+)", body)
