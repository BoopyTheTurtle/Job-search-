"""Command-line entry point: `jobbot sources`, `jobbot searches`, `jobbot crawl`,
`jobbot run`."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated

import typer

from jobbot import __version__
from jobbot.config import load_searches, load_sources
from jobbot.http import SourceError, make_client
from jobbot.sources import available, build

DEFAULT_DB = Path("data/jobbot.sqlite")

SearchOption = Annotated[
    list[str] | None,
    typer.Option(help="Search name from config/searches/; repeatable. Default: all."),
]

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
def searches() -> None:
    """List the searches in config/searches/ and the sources each one queries."""
    for search in load_searches():
        queried = ", ".join(sorted(search.queries)) or "shared sources only"
        typer.echo(f"{search.name:20} {search.label:20} queries: {queried}")


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
    since_days: Annotated[
        int | None,
        typer.Option(help="Only postings newer than N days. Default: since the last run."),
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Print RawJob JSON lines; do not store.")
    ] = False,
    db: Annotated[Path, typer.Option(help="SQLite database path.")] = DEFAULT_DB,
    search: SearchOption = None,
) -> None:
    """Fetch postings, normalize, enrich, dedupe and store them (or print raw with --dry-run)."""
    cfg = load_sources().sources
    chosen = load_searches(names=search)
    if source:
        names = source
    elif all_sources:
        names = sorted(available())
    else:
        names = [n for n, c in cfg.items() if c.enabled]

    if not dry_run:
        from jobbot.pipeline import run_crawl
        from jobbot.store import Store

        with Store(db) as store:
            summary = run_crawl(
                store, names, cfg, searches=chosen, since_days=since_days, limit=limit
            )
        for rec in summary.sources:
            status = (
                rec.error_message
                if rec.skipped
                else (f"ERROR {rec.error_message}" if rec.errors else "ok")
            )
            typer.echo(
                f"{rec.source:20} fetched {rec.fetched:4} new {rec.new:4} "
                f"{rec.duration_ms:6} ms {status}",
                err=True,
            )
        typer.echo(
            f"run {summary.run_id}: {summary.new_jobs} new since {summary.since:%Y-%m-%d} "
            f"→ {db} [{summary.status}]",
            err=True,
        )
        if summary.status != "ok":
            raise typer.Exit(code=1)
        return

    from jobbot.pipeline import missing_env, plan_crawl

    since = datetime.now(tz=UTC) - timedelta(days=since_days if since_days is not None else 14)
    failures = 0
    tasks = plan_crawl(names, cfg, chosen)
    with make_client() as client:
        for task in tasks:
            absent = missing_env(cfg.get(task.source))
            if absent:
                typer.echo(f"{task.label}: skipped: missing {', '.join(absent)}", err=True)
                continue
            try:
                connector = build(task.source, client, task.params)
                count = 0
                for raw in connector.fetch(since, limit):
                    sys.stdout.write(raw.model_dump_json() + "\n")
                    count += 1
                typer.echo(f"{task.label}: {count} postings", err=True)
            except (SourceError, KeyError) as exc:
                failures += 1
                typer.echo(f"{task.label}: FAILED: {exc}", err=True)
    if tasks and failures == len(tasks):
        raise typer.Exit(code=1)


@app.command()
def run(
    source: Annotated[
        list[str] | None, typer.Option(help="Source name; repeatable. Default: all enabled.")
    ] = None,
    limit: Annotated[int | None, typer.Option(help="Max postings per source.")] = None,
    since_days: Annotated[
        int | None,
        typer.Option(help="Only postings newer than N days. Default: since the last run."),
    ] = None,
    db: Annotated[Path, typer.Option(help="SQLite database path.")] = DEFAULT_DB,
    out_dir: Annotated[Path, typer.Option(help="Where digests/ and runs/ are written.")] = Path(
        "data"
    ),
    send: Annotated[
        bool, typer.Option("--send/--no-send", help="Email the digest via Resend if configured.")
    ] = True,
    search: SearchOption = None,
) -> None:
    """Full weekly run: crawl once, then score, write and email one digest per search."""
    from jobbot.run import run_all
    from jobbot.store import Store

    cfg = load_sources().sources
    names = source or [n for n, c in cfg.items() if c.enabled]
    chosen = load_searches(names=search)
    with Store(db) as store:
        result = run_all(
            store,
            chosen,
            names,
            cfg,
            out_dir=out_dir,
            send=send,
            since_days=since_days,
            limit=limit,
        )
    typer.echo(f"run {result.run_id} [{result.status}]: {result.new_jobs} new", err=True)
    for d in result.digests:
        typer.echo(
            f"  {d.search}: {d.strong} strong / {d.possible} possible / {d.senior} senior-only, "
            f"{d.dropped} filtered → {d.digest_path}; email {d.email}",
            err=True,
        )
    if result.status != "ok" or result.email_failed:
        raise typer.Exit(code=1)


def main() -> None:  # pragma: no cover - console script shim
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
