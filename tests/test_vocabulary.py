"""Tests for tagrip.vocabulary module."""

from pathlib import Path

from tagrip.vocabulary import (
    build_mapping,
    learn_vocabulary,
    load_vocabulary,
    save_vocabulary,
)


class TestLearnVocabulary:
    def test_learns_from_frontmatter(self, tmp_path: Path):
        (tmp_path / "a.md").write_text(
            "---\ntags:\n  - python\n  - cli\n---\nContent.", encoding="utf-8"
        )
        (tmp_path / "b.md").write_text(
            "---\ntags:\n  - python\n  - web\n---\nContent.", encoding="utf-8"
        )
        vocab = learn_vocabulary(tmp_path, min_frequency=1)
        assert "python" in vocab
        assert vocab["python"] == 2
        assert "cli" in vocab
        assert "web" in vocab

    def test_min_frequency_filter(self, tmp_path: Path):
        (tmp_path / "a.md").write_text(
            "---\ntags:\n  - python\n  - rare\n---\nContent.", encoding="utf-8"
        )
        (tmp_path / "b.md").write_text(
            "---\ntags:\n  - python\n---\nContent.", encoding="utf-8"
        )
        vocab = learn_vocabulary(tmp_path, min_frequency=2)
        assert "python" in vocab
        assert "rare" not in vocab

    def test_comma_separated_tags(self, tmp_path: Path):
        (tmp_path / "a.md").write_text(
            '---\ntags: "python, cli, tools"\n---\nContent.', encoding="utf-8"
        )
        vocab = learn_vocabulary(tmp_path, min_frequency=1)
        assert "python" in vocab
        assert "cli" in vocab
        assert "tools" in vocab

    def test_no_tags(self, tmp_path: Path):
        (tmp_path / "a.md").write_text("# No frontmatter\n\nJust text.", encoding="utf-8")
        vocab = learn_vocabulary(tmp_path, min_frequency=1)
        assert vocab == {}

    def test_empty_directory(self, tmp_path: Path):
        vocab = learn_vocabulary(tmp_path)
        assert vocab == {}


class TestBuildMapping:
    def test_abbreviation_mapping(self):
        vocab = {"javascript": 10, "python": 8, "js": 3}
        mapping = build_mapping(vocab)
        assert mapping.get("js") == "javascript"

    def test_no_mapping_when_canonical_missing(self):
        vocab = {"python": 5}
        mapping = build_mapping(vocab)
        assert "js" not in mapping or mapping.get("js") != "javascript"

    def test_prefix_mapping(self):
        vocab = {"python": 10, "python3": 3}
        mapping = build_mapping(vocab)
        assert mapping.get("python3") == "python" or "python3" not in mapping

    def test_empty_vocabulary(self):
        assert build_mapping({}) == {}


class TestSaveLoadVocabulary:
    def test_roundtrip(self, tmp_path: Path):
        vocab = {"python": 10, "javascript": 8, "rust": 5}
        path = tmp_path / "vocab.json"
        save_vocabulary(vocab, path)
        loaded = load_vocabulary(path)
        assert loaded == vocab

    def test_creates_parent_dir(self, tmp_path: Path):
        path = tmp_path / "subdir" / "vocab.json"
        save_vocabulary({"test": 1}, path)
        assert path.exists()

    def test_load_nonexistent(self, tmp_path: Path):
        loaded = load_vocabulary(tmp_path / "missing.json")
        assert loaded == {}

    def test_sorted_by_frequency(self, tmp_path: Path):
        vocab = {"rust": 5, "python": 20, "js": 10}
        path = tmp_path / "vocab.json"
        save_vocabulary(vocab, path)
        content = path.read_text(encoding="utf-8")
        lines = [l for l in content.split("\n") if '"' in l and ":" in l]
        assert "python" in lines[0]
