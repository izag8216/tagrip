"""Tests for tagrip.extractor module."""

import math
from pathlib import Path

from tagrip.extractor import (
    _extract_phrases,
    _rake_score,
    _tfidf_score,
    _tokenize,
    build_idf_cache,
    extract_keywords_from_text,
)


class TestTokenize:
    def test_basic_english(self):
        tokens = _tokenize("Hello world this is a test")
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens

    def test_stops_words_removed(self):
        tokens = _tokenize("the quick brown fox is very fast")
        assert "the" not in tokens
        assert "is" not in tokens
        assert "very" not in tokens
        assert "quick" in tokens

    def test_short_words_filtered(self):
        tokens = _tokenize("I a x go")
        assert "go" in tokens
        assert len([t for t in tokens if len(t) <= 1]) == 0

    def test_japanese_characters(self):
        tokens = _tokenize("Pythonのテストです")
        assert "python" in tokens
        assert "テ" in tokens
        assert "ス" in tokens

    def test_empty_text(self):
        assert _tokenize("") == []


class TestTfidfScore:
    def test_basic_scoring(self):
        tokens = ["python", "python", "python", "code", "test"]
        scores = _tfidf_score(tokens)
        assert scores["python"] > scores["code"]
        assert scores["python"] > scores["test"]

    def test_empty_tokens(self):
        assert _tfidf_score([]) == {}

    def test_with_idf_cache(self):
        tokens = ["python", "code", "python"]
        idf = {"python": 2.0, "code": 1.0}
        scores = _tfidf_score(tokens, idf)
        assert scores["python"] > scores["code"]


class TestExtractPhrases:
    def test_basic_phrases(self):
        phrases = _extract_phrases("machine learning model training process")
        assert any("machine learning" in p for p in phrases)
        assert any("learning model" in p for p in phrases)

    def test_empty_text(self):
        assert _extract_phrases("") == []


class TestRakeScore:
    def test_basic_scoring(self):
        phrases = ["machine learning", "machine learning", "deep learning"]
        scores = _rake_score(phrases)
        assert "machine" in scores
        assert scores["machine"] > 0

    def test_empty(self):
        assert _rake_score([]) == {}


class TestExtractKeywordsFromText:
    def test_basic_extraction(self):
        text = """# Python Web Development

Python is a versatile programming language for web development.
Using Django and Flask frameworks, developers can build robust APIs.
Machine learning libraries like scikit-learn and TensorFlow are popular.
"""
        result = extract_keywords_from_text(text, max_keywords=10)
        assert len(result.keywords) > 0
        assert "python" in result.keywords

    def test_heading_boost(self):
        text = "# Machine Learning\n\nSome content about other things."
        result = extract_keywords_from_text(text)
        assert "machine" in result.keywords or "learning" in result.keywords

    def test_wikilink_boost(self):
        text = "Some text [[python-tips]] and [[django-guide]] here."
        result = extract_keywords_from_text(text)
        assert "python-tips" in result.keywords or "django-guide" in result.keywords

    def test_code_language_boost(self):
        text = "```python\ncode\n```\n```javascript\nmore code\n```"
        result = extract_keywords_from_text(text)
        assert "python" in result.keywords or "javascript" in result.keywords

    def test_max_keywords_limit(self):
        text = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"
        result = extract_keywords_from_text(text, max_keywords=3)
        assert len(result.keywords) == 3

    def test_vocabulary_mapping(self):
        text = "# JS Frameworks\n\nUsing js for web development."
        vocab = {"js": "javascript"}
        result = extract_keywords_from_text(text, vocabulary=vocab)
        assert "javascript" in result.keywords

    def test_scores_populated(self):
        text = "# Python Programming\n\nPython is great for data science."
        result = extract_keywords_from_text(text)
        assert len(result.scores) > 0
        for kw in result.keywords:
            assert kw in result.scores

    def test_source_signals(self):
        text = "# My Title\n\n[[link1]] [[link2]]\n\n```python\ncode\n```"
        result = extract_keywords_from_text(text)
        assert "My Title" in result.source_signals["headings"]
        assert "link1" in result.source_signals["wikilinks"]
        assert "python" in result.source_signals["code_languages"]

    def test_empty_text(self):
        result = extract_keywords_from_text("")
        assert result.keywords == []
        assert result.scores == {}


class TestBuildIdfCache:
    def test_builds_from_directory(self, tmp_path: Path):
        (tmp_path / "a.md").write_text("# Python\n\nPython code for testing.", encoding="utf-8")
        (tmp_path / "b.md").write_text("# JavaScript\n\nJavaScript web development.", encoding="utf-8")
        cache = build_idf_cache(tmp_path)
        assert "python" in cache
        assert "javascript" in cache
        assert cache["python"] > 0

    def test_empty_directory(self, tmp_path: Path):
        cache = build_idf_cache(tmp_path)
        assert cache == {}
