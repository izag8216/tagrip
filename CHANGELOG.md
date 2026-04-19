# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-19

### Added

- `extract` command -- keyword extraction from markdown files (TF-IDF + RAKE + structural signals)
- `apply` command -- tag application to YAML frontmatter with merge/replace modes
- `learn` command -- vocabulary building from existing frontmatter tags
- IDF cache for corpus-level keyword discrimination
- Vocabulary mapping for tag synonym canonicalization
- Dry-run mode for previewing tag changes
- CJK (Japanese/Chinese) text support
- Structural signal extraction: headings, wikilinks, code languages
- Batch processing for directories
- JSON, table, and list output formats
- 83 tests with 92% code coverage
