# Contributing

Contributions are welcome! Here's how you can help:

## Development Setup

```bash
git clone https://github.com/izag8216/tagrip.git
cd tagrip
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

## Code Style

- Follow PEP 8
- Use type annotations on all function signatures
- Run `ruff check src/ tests/` before committing
- Maximum line length: 100 characters

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest tests/ -v`)
5. Commit with a clear message
6. Open a pull request

## Bug Reports

Please open an issue with:
- Python version
- tagrip version (`tagrip --version`)
- Steps to reproduce
- Expected vs actual behavior
