"""Tests for tagrip.parser module."""

from pathlib import Path

from tagrip.parser import (
    extract_code_languages,
    extract_headings,
    extract_wikilinks,
    parse_markdown,
    parse_markdown_text,
    strip_markdown_syntax,
)


class TestParseMarkdownText:
    def test_no_frontmatter(self):
        text = "# Hello\n\nSome body text."
        result = parse_markdown_text(text)
        assert result.has_frontmatter is False
        assert result.frontmatter == {}
        assert "# Hello" in result.body

    def test_simple_frontmatter(self):
        text = "---\ntitle: Test\n---\nBody text."
        result = parse_markdown_text(text)
        assert result.has_frontmatter is True
        assert result.frontmatter.get("title") == "Test"
        assert "Body text." in result.body

    def test_frontmatter_with_tags(self):
        text = "---\ntitle: My Note\ntags:\n  - python\n  - cli\n---\nContent here."
        result = parse_markdown_text(text)
        assert result.has_frontmatter is True
        tags = result.frontmatter.get("tags")
        assert isinstance(tags, list)
        assert "python" in tags
        assert "cli" in tags

    def test_empty_frontmatter(self):
        text = "---\n---\nJust body."
        result = parse_markdown_text(text)
        assert result.has_frontmatter is True
        assert "Just body." in result.body

    def test_unclosed_frontmatter(self):
        text = "---\ntitle: Oops\nNo closing"
        result = parse_markdown_text(text)
        assert result.has_frontmatter is False

    def test_preserves_yaml_types(self):
        text = "---\ntitle: Hello\ncount: 42\npublished: true\n---\nBody"
        result = parse_markdown_text(text)
        assert result.frontmatter.get("title") == "Hello"
        assert result.frontmatter.get("count") == "42"
        assert result.frontmatter.get("published") == "true"


class TestStripMarkdownSyntax:
    def test_removes_code_blocks(self):
        text = "Before ```python\nprint('hi')\n``` After"
        result = strip_markdown_syntax(text)
        assert "print" not in result
        assert "Before" in result
        assert "After" in result

    def test_removes_inline_code(self):
        text = "Use `tagrip` to extract"
        result = strip_markdown_syntax(text)
        assert "tagrip" in result
        assert "`" not in result

    def test_removes_images(self):
        text = "![alt](image.png) some text"
        result = strip_markdown_syntax(text)
        assert "image.png" not in result
        assert "some text" in result

    def test_extracts_link_text(self):
        text = "Click [here](https://example.com)"
        result = strip_markdown_syntax(text)
        assert "here" in result
        assert "example.com" not in result

    def test_removes_headings(self):
        text = "## Section Title\nSome content"
        result = strip_markdown_syntax(text)
        assert "Section Title" in result
        assert "##" not in result

    def test_removes_bold_italic(self):
        text = "**bold** and *italic* and ~~strikethrough~~"
        result = strip_markdown_syntax(text)
        assert "bold" in result
        assert "italic" in result
        assert "strikethrough" in result
        assert "**" not in result
        assert "*" not in result

    def test_removes_list_markers(self):
        text = "- item one\n- item two\n1. numbered"
        result = strip_markdown_syntax(text)
        assert "item one" in result
        assert "- " not in result

    def test_removes_blockquotes(self):
        text = "> quoted text"
        result = strip_markdown_syntax(text)
        assert "quoted text" in result
        assert ">" not in result

    def test_collapses_whitespace(self):
        text = "multiple   spaces   here"
        result = strip_markdown_syntax(text)
        assert "multiple spaces here" in result


class TestExtractHeadings:
    def test_single_heading(self):
        assert extract_headings("# Hello") == ["Hello"]

    def test_multiple_headings(self):
        text = "## One\n\n## Two\n\n### Three"
        headings = extract_headings(text)
        assert headings == ["One", "Two", "Three"]

    def test_no_headings(self):
        assert extract_headings("Just text") == []

    def test_strips_formatting(self):
        assert extract_headings("## **Bold Title**") == ["Bold Title"]


class TestExtractWikilinks:
    def test_simple_wikilink(self):
        assert extract_wikilinks("[[python]]") == ["python"]

    def test_wikilink_with_alias(self):
        assert extract_wikilinks("[[python|Python Lang]]") == ["python"]

    def test_multiple_wikilinks(self):
        text = "[[tag1]] and [[tag2]] and [[tag3|alias]]"
        links = extract_wikilinks(text)
        assert links == ["tag1", "tag2", "tag3"]

    def test_no_wikilinks(self):
        assert extract_wikilinks("plain text") == []


class TestExtractCodeLanguages:
    def test_single_block(self):
        assert extract_code_languages("```python\ncode\n```") == ["python"]

    def test_multiple_blocks(self):
        text = "```js\ncode\n```\n```typescript\ncode\n```"
        langs = extract_code_languages(text)
        assert langs == ["js", "typescript"]

    def test_no_code_blocks(self):
        assert extract_code_languages("no code") == []
