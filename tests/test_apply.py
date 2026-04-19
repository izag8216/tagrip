"""Tests for tagrip.apply module."""

from pathlib import Path

from tagrip.apply import apply_tags


class TestApplyTags:
    def test_add_tags_to_file_with_frontmatter(self, tmp_path: Path):
        md = tmp_path / "test.md"
        md.write_text("---\ntitle: Test\n---\nBody text.", encoding="utf-8")
        result = apply_tags(md, ["python", "cli"])
        assert "python" in result["added"]
        assert "cli" in result["added"]
        content = md.read_text(encoding="utf-8")
        assert "python" in content
        assert "cli" in content

    def test_add_tags_to_file_without_frontmatter(self, tmp_path: Path):
        md = tmp_path / "test.md"
        md.write_text("# Hello\n\nBody text.", encoding="utf-8")
        result = apply_tags(md, ["python"])
        assert "python" in result["added"]
        content = md.read_text(encoding="utf-8")
        assert "python" in content
        assert "---" in content

    def test_dry_run_no_write(self, tmp_path: Path):
        md = tmp_path / "test.md"
        md.write_text("---\ntitle: Test\n---\nBody text.", encoding="utf-8")
        original = md.read_text(encoding="utf-8")
        result = apply_tags(md, ["python"], dry_run=True)
        assert "python" in result["added"]
        assert md.read_text(encoding="utf-8") == original

    def test_merge_with_existing(self, tmp_path: Path):
        md = tmp_path / "test.md"
        md.write_text("---\ntags:\n  - python\n---\nBody.", encoding="utf-8")
        result = apply_tags(md, ["python", "cli"], merge=True)
        assert result["existing"] == ["python"]
        assert result["added"] == ["cli"]
        content = md.read_text(encoding="utf-8")
        assert content.count("python") >= 1
        assert "cli" in content

    def test_replace_mode(self, tmp_path: Path):
        md = tmp_path / "test.md"
        md.write_text("---\ntags:\n  - old\n---\nBody.", encoding="utf-8")
        result = apply_tags(md, ["new"], merge=False)
        assert "new" in result["added"]
        content = md.read_text(encoding="utf-8")
        assert "new" in content

    def test_no_duplicate_tags(self, tmp_path: Path):
        md = tmp_path / "test.md"
        md.write_text("---\ntags:\n  - python\n---\nBody.", encoding="utf-8")
        result = apply_tags(md, ["python"], merge=True)
        assert result["added"] == []
        content = md.read_text(encoding="utf-8")
        assert content.count("python") == 1

    def test_case_insensitive_dedup(self, tmp_path: Path):
        md = tmp_path / "test.md"
        md.write_text("---\ntags:\n  - Python\n---\nBody.", encoding="utf-8")
        result = apply_tags(md, ["python"], merge=True)
        assert result["added"] == []

    def test_preserves_other_frontmatter(self, tmp_path: Path):
        md = tmp_path / "test.md"
        md.write_text("---\ntitle: My Note\nauthor: test\n---\nBody.", encoding="utf-8")
        apply_tags(md, ["python"])
        content = md.read_text(encoding="utf-8")
        assert "title: My Note" in content
        assert "author: test" in content
