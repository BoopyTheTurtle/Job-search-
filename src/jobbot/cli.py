"""Command-line entry point: `jobbot sources`, `jobbot crawl`."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from typing import Annotated

import typer

from jobbot import __version__
from jobbot.config import load_sources
from jobbot.http import SourceError, make_client
from jobbot.sources import available, build

app = typer.Typer(no_args_is_help=True, help=f"jobbot {__version__}")


@app.command()
def sources() -> None:
    """List registered connectors and whether they are enabled in config/sources.yaml."""
    cfg = load_sources().sources
    for name in sorted(available()):
        entry = cfg.get(name)
        state = "enabled" if entry and entry.enabled else ("disabled" if entry else "unconfigured")
        tier = entry.tier if entry else "-"
        typer.echo(f"{name:20} tier {tier:2} {state}")


@app.command()
def crawl(
    source: Annotated[
        list[str] | None, typer.Option(help="Source name; repeatable. Default: all enabled.")
    ] = None,
    all_sources: Annotated[
        bool,
        typer.Option(
            "--all", help="Crawl every registered connector, including ones disabled in config."
        ),
    ] = False,
    limit: Annotated[int | None, typer.Option(help="Max postings per source.")] = None,
    since_days: Annotated[int, typer.Option(help="Only postings newer than N days.")] = 14,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Print RawJob JSON lines; do not store.")
    ] = False,
) -> None:
    """Fetch postings from one or more sources. Phase 0 supports --dry-run only."""
    if not dry_run:
        typer.echo("Storing results is not implemented yet (Phase 1). Use --dry-run.", err=True)
        raise typer.Exit(code=2)

    cfg = load_sources().sources
    if source:
        names = source
    elif all_sources:
        names = sorted(available())
    else:
        names = [n for n, c in cfg.items() if c.enabled]
    since = datetime.now(tz=UTC) - timedelta(days=since_days)
    failures = 0
    with make_client() as client:
        for name in names:
            entry = cfg.get(name)
            params = entry.params if entry else {}
            try:
                connector = build(name, client, params)
                count = 0
                for raw in connector.fetch(since, limit):
                    sys.stdout.write(raw.model_dump_json() + "\n")
                    count += 1
                typer.echo(f"{name}: {count} postings", err=True)
            except (SourceError, KeyError) as exc:
                failures += 1
                typer.echo(f"{name}: FAILED: {exc}", err=True)
    if names and failures == len(names):
        raise typer.Exit(code=1)


def main() -> None:  # pragma: no cover - console script shim
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
