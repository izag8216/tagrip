"""Vocabulary management -- learn and map tags from existing markdown files."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .parser import parse_markdown


def learn_vocabulary(directory: Path, min_frequency: int = 2) -> dict[str, int]:
    """Scan markdown files and collect tag frequency from frontmatter."""
    tag_counter: Counter[str] = Counter()
    md_files = list(directory.rglob("*.md"))

    for md_file in md_files:
        try:
            parsed = parse_markdown(md_file)
            tags = parsed.frontmatter.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]
            if isinstance(tags, list):
                for tag in tags:
                    if isinstance(tag, str) and tag.strip():
                        tag_counter[tag.strip().lower()] += 1
        except (OSError, UnicodeDecodeError):
            continue

    return {tag: count for tag, count in tag_counter.items() if count >= min_frequency}


def build_mapping(vocabulary: dict[str, int], threshold: float = 0.8) -> dict[str, str]:
    """Build alias-to-canonical mapping from vocabulary.

    Maps similar tags (e.g., 'python3' -> 'python', 'js' -> 'javascript')
    based on prefix matching and common abbreviations.
    """
    abbreviations: dict[str, str] = {
        "js": "javascript",
        "ts": "typescript",
        "py": "python",
        "rb": "ruby",
        "go": "golang",
        "k8s": "kubernetes",
        "k8": "kubernetes",
        "ai": "artificial-intelligence",
        "ml": "machine-learning",
        "dl": "deep-learning",
        "nlp": "natural-language-processing",
        "cli": "command-line",
        "ui": "user-interface",
        "ux": "user-experience",
        "ci": "continuous-integration",
        "cd": "continuous-deployment",
        "db": "database",
        "cfg": "configuration",
        "config": "configuration",
        "auth": "authentication",
        "authz": "authorization",
    }

    mapping: dict[str, str] = {}
    sorted_tags = sorted(vocabulary.keys(), key=lambda t: vocabulary.get(t, 0), reverse=True)

    for tag in sorted_tags:
        canonical = abbreviations.get(tag)
        if canonical:
            if canonical in vocabulary:
                mapping[tag] = canonical
            continue

        for existing in sorted_tags:
            if existing == tag:
                continue
            if existing.startswith(tag) or tag.startswith(existing):
                if len(tag) < len(existing):
                    if vocabulary.get(existing, 0) >= vocabulary.get(tag, 0):
                        mapping[tag] = existing
                elif vocabulary.get(tag, 0) < vocabulary.get(existing, 0):
                    mapping[tag] = existing

    return mapping


def save_vocabulary(vocabulary: dict[str, int], path: Path) -> None:
    """Save vocabulary to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sorted_vocab = dict(sorted(vocabulary.items(), key=lambda x: x[1], reverse=True))
    path.write_text(json.dumps(sorted_vocab, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_vocabulary(path: Path) -> dict[str, int]:
    """Load vocabulary from JSON file."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
