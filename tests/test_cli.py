"""Tests for tagrip CLI integration."""

from pathlib import Path

from click.testing import CliRunner

from tagrip.cli import main


class TestExtractCommand:
    def test_extract_table_format(self, tmp_path: Path):
        md = tmp_path / "test.md"
        md.write_text(
            "---\ntitle: Python Guide\n---\n# Python Web Development\n\n"
            "Python is great for building web APIs with Django and Flask.\n"
            "Machine learning with scikit-learn and TensorFlow.\n",
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(main, ["extract", str(md)])
        assert result.exit_code == 0
        assert "python" in result.output.lower()

    def test_extract_json_format(self, tmp_path: Path):
        md = tmp_path / "test.md"
        md.write_text("# Test\n\nSome content about python programming.", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, ["extract", str(md), "--format", "json"])
        assert result.exit_code == 0
        assert '"keywords"' in result.output

    def test_extract_list_format(self, tmp_path: Path):
        md = tmp_path / "test.md"
        md.write_text("# Test\n\nPython programming content.", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, ["extract", str(md), "--format", "list"])
        assert result.exit_code == 0
        lines = [l for l in result.output.strip().split("\n") if l.strip()]
        assert len(lines) > 0

    def test_extract_max_keywords(self, tmp_path: Path):
        md = tmp_path / "test.md"
        md.write_text(
            "# Alpha Beta Gamma Delta Epsilon Zeta\n\n"
            "Alpha beta gamma delta epsilon zeta eta theta.",
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(main, ["extract", str(md), "--max", "3", "--format", "list"])
        assert result.exit_code == 0
        lines = [l for l in result.output.strip().split("\n") if l.strip()]
        assert len(lines) <= 3

    def test_extract_nonexistent_file(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(main, ["extract", str(tmp_path / "missing.md")])
        assert result.exit_code == 1

    def test_extract_with_vocab(self, tmp_path: Path):
        md = tmp_path / "test.md"
        md.write_text("# JS Development\n\nUsing js for web apps.", encoding="utf-8")
        vocab = tmp_path / "vocab.json"
        vocab.write_text('{"javascript": 10}', encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, ["extract", str(md), "--vocab", str(vocab), "--format", "list"])
        assert result.exit_code == 0


class TestApplyCommand:
    def test_apply_dry_run(self, tmp_path: Path):
        md = tmp_path / "test.md"
        md.write_text("# Python\n\nPython is great.\n", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, ["apply", str(md), "--dry-run"])
        assert result.exit_code == 0
        assert "DRY RUN" in result.output or "no new tags" in result.output.lower() or "+" in result.output

    def test_apply_to_directory(self, tmp_path: Path):
        (tmp_path / "a.md").write_text("# Python\n\nPython code.", encoding="utf-8")
        (tmp_path / "b.md").write_text("# Rust\n\nRust code.", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, ["apply", str(tmp_path), "--dry-run"])
        assert result.exit_code == 0

    def test_apply_no_markdown_files(self, tmp_path: Path):
        (tmp_path / "data.txt").write_text("Not markdown", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, ["apply", str(tmp_path)])
        assert "No markdown files" in result.output or result.exit_code == 0


class TestLearnCommand:
    def test_learn_from_directory(self, tmp_path: Path):
        (tmp_path / "a.md").write_text(
            "---\ntags:\n  - python\n  - cli\n---\nContent.", encoding="utf-8"
        )
        (tmp_path / "b.md").write_text(
            "---\ntags:\n  - python\n---\nContent.", encoding="utf-8"
        )
        output = tmp_path / "vocab.json"
        runner = CliRunner()
        result = runner.invoke(main, ["learn", str(tmp_path), "--min-freq", "1", "-o", str(output)])
        assert result.exit_code == 0
        assert "python" in result.output

    def test_learn_requires_directory(self, tmp_path: Path):
        md = tmp_path / "single.md"
        md.write_text("---\ntags:\n  - test\n---\nContent.", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, ["learn", str(md)])
        assert result.exit_code == 1

    def test_learn_no_tags(self, tmp_path: Path):
        (tmp_path / "a.md").write_text("# No tags\n\nJust text.", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, ["learn", str(tmp_path)])
        assert "No tags" in result.output or result.exit_code == 0


class TestVersionCommand:
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert "tagrip" in result.output
        assert result.exit_code == 0
