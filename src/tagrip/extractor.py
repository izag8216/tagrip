"""Keyword extraction engine -- TF-IDF + RAKE + pattern matching."""

from __future__ import annotations

import math
import re
import string
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .parser import (
    extract_code_languages,
    extract_headings,
    extract_wikilinks,
    parse_markdown,
    strip_markdown_syntax,
)


@dataclass(frozen=True)
class ExtractionResult:
    keywords: list[str]
    scores: dict[str, float]
    source_signals: dict[str, list[str]] = field(default_factory=dict)


STOP_WORDS: frozenset[str] = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "is", "it", "as", "be", "was", "are", "been", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might", "can",
    "this", "that", "these", "those", "not", "no", "nor", "so", "if", "then", "than",
    "too", "very", "just", "about", "also", "into", "over", "after", "before", "between",
    "through", "during", "without", "within", "along", "across", "behind", "beyond",
    "plus", "except", "up", "out", "around", "down", "off", "above", "near",
    "its", "my", "your", "his", "her", "our", "their", "what", "which", "who", "whom",
    "how", "when", "where", "why", "all", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "any", "only", "same",
    # Japanese particles/common words
    "の", "に", "は", "を", "た", "が", "で", "て", "と", "し", "れ", "さ", "ある",
    "いる", "も", "する", "から", "な", "こと", "として", "い", "や", "れる",
    "か", "なっ", "なく", "なかっ", "なら", "なり", "なり", "なる", "へ", "です",
    "ました", "ません", "だ", "だった", "だったら", "では", "また", "まだ", "だけ",
})


def _tokenize(text: str) -> list[str]:
    """Tokenize text into words, handling CJK characters."""
    tokens: list[str] = []
    # Split CJK and Latin to avoid mixed tokens like "pythonのテスト"
    separated = re.sub(r"([\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff])", r" \1 ", text)
    for word in re.findall(r"[a-zA-Z][\w-]*", separated.lower()):
        if word not in STOP_WORDS and len(word) > 1:
            tokens.append(word)
    for char in text:
        if "\u4e00" <= char <= "\u9fff" or "\u3040" <= char <= "\u309f" or "\u30a0" <= char <= "\u30ff":
            tokens.append(char)
    return tokens


def _extract_phrases(text: str) -> list[str]:
    """Extract candidate phrases (2-3 word sequences) from text."""
    sentences = re.split(r"[.!?。！？\n]+", text)
    phrases: list[str] = []
    for sentence in sentences:
        words = [
            w.lower()
            for w in re.findall(r"[a-zA-Z]+[\w-]*", sentence)
            if w.lower() not in STOP_WORDS and len(w) > 1
        ]
        for n in (2, 3):
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i : i + n])
                if not all(w in string.punctuation for w in phrase):
                    phrases.append(phrase)
    return phrases


def _tfidf_score(tokens: list[str], idf_cache: dict[str, float] | None = None) -> dict[str, float]:
    """Compute TF-IDF scores for tokens."""
    if not tokens:
        return {}
    counter = Counter(tokens)
    total = len(tokens)
    tf = {word: count / total for word, count in counter.items()}
    if idf_cache:
        return {
            word: freq * idf_cache.get(word, math.log(2))
            for word, freq in tf.items()
            if word in idf_cache
        }
    return {word: freq for word, freq in tf.items()}


def _rake_score(phrases: list[str]) -> dict[str, float]:
    """Simplified RAKE scoring: word degree / frequency."""
    if not phrases:
        return {}
    word_freq: Counter[str] = Counter()
    word_degree: Counter[str] = Counter()
    for phrase in phrases:
        words = phrase.split()
        degree = len(words) - 1
        for word in words:
            word_freq[word] += 1
            word_degree[word] += degree
    scores: dict[str, float] = {}
    for word, freq in word_freq.items():
        scores[word] = (word_degree[word] + freq) / freq
    for phrase in phrases:
        words = phrase.split()
        scores[phrase] = sum(scores.get(w, 0.0) for w in words) / len(words)
    return scores


def extract_keywords(
    path: Path,
    max_keywords: int = 15,
    idf_cache: dict[str, float] | None = None,
    vocabulary: dict[str, str] | None = None,
) -> ExtractionResult:
    """Extract keywords from a markdown file using TF-IDF + RAKE + structural signals."""
    parsed = parse_markdown(path)
    clean_text = strip_markdown_syntax(parsed.body)
    tokens = _tokenize(clean_text)
    phrases = _extract_phrases(clean_text)

    tfidf_scores = _tfidf_score(tokens, idf_cache)
    rake_scores = _rake_score(phrases)

    combined: dict[str, float] = {}
    for word, score in tfidf_scores.items():
        combined[word] = combined.get(word, 0.0) + score * 0.4
    for phrase, score in rake_scores.items():
        combined[phrase] = combined.get(phrase, 0.0) + score * 0.3

    headings = extract_headings(parsed.body)
    for heading in headings:
        heading_words = _tokenize(heading)
        for word in heading_words:
            combined[word] = combined.get(word, 0.0) + 0.5

    wikilinks = extract_wikilinks(parsed.body)
    for link in wikilinks:
        link_slug = link.strip().lower().replace(" ", "-")
        combined[link_slug] = combined.get(link_slug, 0.0) + 0.6

    code_langs = extract_code_languages(parsed.body)
    for lang in code_langs:
        combined[lang] = combined.get(lang, 0.0) + 0.3

    if vocabulary:
        mapped: dict[str, float] = {}
        for kw, score in combined.items():
            canonical = vocabulary.get(kw, vocabulary.get(kw.lower(), kw))
            mapped[canonical] = mapped.get(canonical, 0.0) + score
        combined = mapped

    sorted_keywords = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    top_keywords = [kw for kw, _ in sorted_keywords[:max_keywords]]

    return ExtractionResult(
        keywords=top_keywords,
        scores=dict(sorted_keywords[:max_keywords]),
        source_signals={
            "headings": headings[:5],
            "wikilinks": wikilinks[:10],
            "code_languages": code_langs[:5],
        },
    )


def extract_keywords_from_text(
    text: str,
    max_keywords: int = 15,
    idf_cache: dict[str, float] | None = None,
    vocabulary: dict[str, str] | None = None,
) -> ExtractionResult:
    """Extract keywords from raw markdown text (for testing without files)."""
    clean_text = strip_markdown_syntax(text)
    tokens = _tokenize(clean_text)
    phrases = _extract_phrases(clean_text)

    tfidf_scores = _tfidf_score(tokens, idf_cache)
    rake_scores = _rake_score(phrases)

    combined: dict[str, float] = {}
    for word, score in tfidf_scores.items():
        combined[word] = combined.get(word, 0.0) + score * 0.4
    for phrase, score in rake_scores.items():
        combined[phrase] = combined.get(phrase, 0.0) + score * 0.3

    headings = extract_headings(text)
    for heading in headings:
        for word in _tokenize(heading):
            combined[word] = combined.get(word, 0.0) + 0.5

    wikilinks = extract_wikilinks(text)
    for link in wikilinks:
        link_slug = link.strip().lower().replace(" ", "-")
        combined[link_slug] = combined.get(link_slug, 0.0) + 0.6

    code_langs = extract_code_languages(text)
    for lang in code_langs:
        combined[lang] = combined.get(lang, 0.0) + 0.3

    if vocabulary:
        mapped: dict[str, float] = {}
        for kw, score in combined.items():
            canonical = vocabulary.get(kw, vocabulary.get(kw.lower(), kw))
            mapped[canonical] = mapped.get(canonical, 0.0) + score
        combined = mapped

    sorted_keywords = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    top_keywords = [kw for kw, _ in sorted_keywords[:max_keywords]]

    return ExtractionResult(
        keywords=top_keywords,
        scores=dict(sorted_keywords[:max_keywords]),
        source_signals={
            "headings": headings[:5],
            "wikilinks": wikilinks[:10],
            "code_languages": code_langs[:5],
        },
    )


def build_idf_cache(directory: Path) -> dict[str, float]:
    """Build IDF cache from all markdown files in a directory."""
    md_files = list(directory.rglob("*.md"))
    if not md_files:
        return {}
    doc_count = len(md_files)
    doc_freq: Counter[str] = Counter()
    for md_file in md_files:
        try:
            parsed = parse_markdown(md_file)
            clean = strip_markdown_syntax(parsed.body)
            tokens = set(_tokenize(clean))
            for token in tokens:
                doc_freq[token] += 1
        except (OSError, UnicodeDecodeError):
            continue
    return {
        word: math.log((doc_count + 1) / (freq + 1)) + 1
        for word, freq in doc_freq.items()
    }
