"""CLI entry point for tagrip."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from . import __version__
from .apply import apply_tags
from .extractor import build_idf_cache, extract_keywords, extract_keywords_from_text
from .vocabulary import (
    build_mapping,
    learn_vocabulary,
    load_vocabulary,
    save_vocabulary,
)

console = Console()

DEFAULT_VOCAB_PATH = Path.home() / ".tagrip" / "vocabulary.json"


@click.group()
@click.version_option(__version__, prog_name="tagrip")
@click.pass_context
def main(ctx: click.Context) -> None:
    """Smart tag & keyword extractor for Markdown."""


@main.command()
@click.argument("path", type=Path)
@click.option("--max", "-n", "max_keywords", type=int, default=15, help="Max keywords to extract.")
@click.option("--format", "fmt", type=click.Choice(["table", "json", "list"]), default="table")
@click.option("--vocab", type=Path, default=None, help="Vocabulary file for tag mapping.")
@click.pass_context
def extract(
    ctx: click.Context,
    path: Path,
    max_keywords: int,
    fmt: str,
    vocab: Path | None,
) -> None:
    """Extract keywords from a markdown file."""
    if not path.exists():
        console.print(f"[red]Error: {path} not found.[/red]")
        sys.exit(1)

    vocabulary = None
    if vocab and vocab.exists():
        vocab_data = load_vocabulary(vocab)
        vocabulary = build_mapping(vocab_data)

    result = extract_keywords(path, max_keywords=max_keywords, vocabulary=vocabulary)

    if fmt == "json":
        import json
        click.echo(json.dumps({
            "keywords": result.keywords,
            "scores": {k: round(v, 4) for k, v in result.scores.items()},
            "signals": result.source_signals,
        }, indent=2, ensure_ascii=False))
    elif fmt == "list":
        for kw in result.keywords:
            click.echo(kw)
    else:
        console.print(f"\n[bold]Keywords from {path.name}[/bold]\n")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("#", justify="right", width=4)
        table.add_column("Keyword", style="cyan")
        table.add_column("Score", justify="right", style="green")
        for i, kw in enumerate(result.keywords, 1):
            score = result.scores.get(kw, 0.0)
            table.add_row(str(i), kw, f"{score:.4f}")
        console.print(table)

        if result.source_signals.get("headings"):
            console.print("\n[dim]Headings:[/dim] " + ", ".join(result.source_signals["headings"]))
        if result.source_signals.get("wikilinks"):
            console.print("[dim]Wikilinks:[/dim] " + ", ".join(result.source_signals["wikilinks"]))
        if result.source_signals.get("code_languages"):
            console.print("[dim]Code:[/dim] " + ", ".join(result.source_signals["code_languages"]))


@main.command()
@click.argument("path", type=Path)
@click.option("--dry-run", is_flag=True, help="Preview changes without writing files.")
@click.option("--max", "-n", "max_keywords", type=int, default=10, help="Max tags per file.")
@click.option("--vocab", type=Path, default=None, help="Vocabulary file.")
@click.option("--idf", is_flag=True, help="Build IDF cache from directory for better scoring.")
@click.option("--merge/--replace", default=True, help="Merge with existing tags or replace.")
@click.pass_context
def apply(
    ctx: click.Context,
    path: Path,
    dry_run: bool,
    max_keywords: int,
    vocab: Path | None,
    idf: bool,
    merge: bool,
) -> None:
    """Apply extracted tags to markdown file(s)."""
    vocabulary = None
    if vocab and vocab.exists():
        vocab_data = load_vocabulary(vocab)
        vocabulary = build_mapping(vocab_data)

    idf_cache = None
    if idf and path.is_dir():
        console.print("[dim]Building IDF cache from directory...[/dim]")
        idf_cache = build_idf_cache(path)

    files = [path] if path.is_file() else sorted(path.rglob("*.md"))
    if not files:
        console.print(f"[yellow]No markdown files found at {path}[/yellow]")
        return

    total_added = 0
    for md_file in files:
        try:
            result = extract_keywords(
                md_file, max_keywords=max_keywords, idf_cache=idf_cache, vocabulary=vocabulary
            )
            changes = apply_tags(md_file, result.keywords, dry_run=dry_run, merge=merge)

            if changes["added"]:
                prefix = "[yellow]DRY RUN[/yellow] " if dry_run else ""
                console.print(
                    f"{prefix}[green]+{len(changes['added'])}[/green] tags for {md_file.relative_to(path.parent if path.is_dir() else path.parent)}: "
                    + ", ".join(changes["added"][:5])
                    + (f" [+{len(changes['added']) - 5} more]" if len(changes["added"]) > 5 else "")
                )
                total_added += len(changes["added"])
            else:
                if dry_run:
                    console.print(f"[dim]  {md_file.name}: no new tags needed[/dim]")
        except (OSError, UnicodeDecodeError) as e:
            console.print(f"[red]Error processing {md_file}: {e}[/red]")

    action = "would be " if dry_run else ""
    console.print(f"\n[bold]Total: {total_added} tags {action}added across {len(files)} files.[/bold]")


@main.command()
@click.argument("path", type=Path)
@click.option("--min-freq", type=int, default=2, help="Minimum tag frequency to include.")
@click.option("--output", "-o", type=Path, default=None, help="Output vocabulary file.")
@click.pass_context
def learn(
    ctx: click.Context,
    path: Path,
    min_freq: int,
    output: Path | None,
) -> None:
    """Build tag vocabulary from existing markdown frontmatter."""
    if not path.is_dir():
        console.print(f"[red]Error: {path} must be a directory.[/red]")
        sys.exit(1)

    console.print(f"[dim]Scanning {path} for tags...[/dim]")
    vocabulary = learn_vocabulary(path, min_frequency=min_freq)

    if not vocabulary:
        console.print("[yellow]No tags found in frontmatter.[/yellow]")
        return

    output_path = output or DEFAULT_VOCAB_PATH
    save_vocabulary(vocabulary, output_path)

    console.print(f"\n[bold]Vocabulary: {len(vocabulary)} tags learned[/bold]\n")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Tag", style="cyan")
    table.add_column("Frequency", justify="right", style="green")
    for tag, count in sorted(vocabulary.items(), key=lambda x: x[1], reverse=True)[:20]:
        table.add_row(tag, str(count))
    console.print(table)
    if len(vocabulary) > 20:
        console.print(f"[dim]... and {len(vocabulary) - 20} more[/dim]")
    console.print(f"\n[green]Saved to {output_path}[/green]")


if __name__ == "__main__":
    main()
