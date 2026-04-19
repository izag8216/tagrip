[![header](https://capsule-render.vercel.app/api?section=header&type=venom&color=0:2D5A27,50:1B6B3A,100:3A6B8C&fontColor=FFFFFF&height=240&fontSize=52&fontAlignY=42&text=tagrip&desc=Smart+Tag+%26+Keyword+Extractor+for+Markdown&descSize=17&descAlignY=62&descAlign=center)](https://github.com/izag8216/tagrip)

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-83%20passing-brightgreen?style=flat-square)](tests/)
[![Coverage](https://img.shields.io/badge/Coverage-92%25-brightgreen?style=flat-square)](tests/)

**[日本語](README.ja.md)**

Smart tag & keyword extractor for Markdown files. Uses TF-IDF + RAKE + structural signals (headings, wikilinks, code blocks) to generate relevant tags, then writes them to YAML frontmatter. Learns from your existing tag vocabulary.

## Features

- **Multi-signal extraction** -- TF-IDF, RAKE phrases, heading boost, wikilink detection, code language signals
- **Frontmatter-aware** -- reads and writes YAML frontmatter tags without touching the rest
- **Vocabulary learning** -- scan your vault to build a tag vocabulary, then map synonyms automatically
- **Dry-run mode** -- preview tag changes before committing
- **Batch processing** -- apply tags to an entire directory of markdown files
- **IDF weighting** -- build corpus-level IDF cache for better keyword discrimination
- **CJK support** -- handles Japanese and Chinese text alongside English
- **Zero config** -- works out of the box, no API keys or cloud services

## Installation

```bash
pip install tagrip
```

Or with [pipx](https://pypa.github.io/pipx/) (recommended for CLI tools):

```bash
pipx install tagrip
```

Or from source:

```bash
git clone https://github.com/izag8216/tagrip.git
cd tagrip
pip install -e .
```

## Quick Start

```bash
# Extract keywords from a markdown file
tagrip extract article.md

# Preview tag application (dry run)
tagrip apply article.md --dry-run

# Apply tags to a single file
tagrip apply article.md

# Apply tags to an entire vault
tagrip apply ./vault/ --dry-run
tagrip apply ./vault/ --idf

# Learn vocabulary from existing tags
tagrip learn ./vault/ --min-freq 2

# Use vocabulary for tag mapping
tagrip extract article.md --vocab ~/.tagrip/vocabulary.json
tagrip apply ./vault/ --vocab ~/.tagrip/vocabulary.json

# Output as JSON
tagrip extract article.md --format json

# Output as plain list
tagrip extract article.md --format list -n 5
```

## Commands

| Command | Description |
|---------|-------------|
| `extract <path>` | Extract keywords from a markdown file |
| `apply <path>` | Apply extracted tags to file(s) |
| `learn <dir>` | Build tag vocabulary from frontmatter |

### Extract Options

| Option | Default | Description |
|--------|---------|-------------|
| `--max`, `-n` | 15 | Maximum keywords to extract |
| `--format` | `table` | Output format: `table`, `json`, `list` |
| `--vocab` | None | Vocabulary file for tag mapping |

### Apply Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dry-run` | off | Preview changes without writing |
| `--max`, `-n` | 10 | Maximum tags per file |
| `--vocab` | None | Vocabulary file |
| `--idf` | off | Build IDF cache for better scoring |
| `--merge` | on | Merge with existing tags |
| `--replace` | off | Replace existing tags entirely |

### Learn Options

| Option | Default | Description |
|--------|---------|-------------|
| `--min-freq` | 2 | Minimum tag frequency to include |
| `--output`, `-o` | `~/.tagrip/vocabulary.json` | Output vocabulary file |

## How It Works

1. **Parse** -- Reads markdown file, separates YAML frontmatter from body text
2. **Clean** -- Strips markdown syntax (code blocks, links, formatting) for analysis
3. **Tokenize** -- Splits text into words with CJK character support
4. **Score** -- Combines three scoring signals:
   - **TF-IDF** (40%) -- term frequency with optional corpus-level IDF weighting
   - **RAKE** (30%) -- rapid automatic keyword extraction for multi-word phrases
   - **Structural** -- heading text (+0.5), wikilinks (+0.6), code languages (+0.3)
5. **Map** -- Applies vocabulary mapping to canonicalize tags (e.g., `js` -> `javascript`)
6. **Apply** -- Writes curated tags to frontmatter, preserving all other YAML fields

## Example Output

```
$ tagrip extract python-guide.md

Keywords from python-guide.md

#  Keyword          Score
1  python           0.3842
2  django           0.2156
3  web development  0.1834
4  api              0.1521
5  flask            0.1287
6  machine learning 0.1145

Headings: Python Web Development, API Design
Wikilinks: django-rest, flask-guide
Code: python, javascript
```

## Requirements

- Python 3.10+
- Dependencies: click, rich, pyyaml, scikit-learn, rake-nltk, nltk

## License

MIT License -- see [LICENSE](LICENSE) for details.
