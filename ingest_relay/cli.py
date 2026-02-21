from __future__ import annotations

import json

import typer
import uvicorn

from ingest_relay.init_db import init_db
from ingest_relay.services.pipeline import run_connector
from ingest_relay.settings import get_settings
from ingest_relay.utils.logging import configure_logging

app = typer.Typer(help="IngestRelay command line interface")


@app.command("init-db")
def init_db_command() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    init_db()
    typer.echo("Database tables initialized")


@app.command("run")
def run_command(
    connector: str = typer.Option(..., help="Path to connector YAML"),
    push_run_id: str | None = typer.Option(None, help="Existing push run id to process"),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    result = run_connector(connector, push_run_id=push_run_id)
    typer.echo(json.dumps(result.__dict__, sort_keys=True))


@app.command("serve")
def serve_command(
    host: str = typer.Option("0.0.0.0"),
    port: int = typer.Option(8080),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    uvicorn.run("ingest_relay.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
