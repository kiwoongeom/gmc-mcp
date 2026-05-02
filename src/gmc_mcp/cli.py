"""CLI entrypoint exposed as the `gmc-mcp` console script.

Subcommands:

* `gmc-mcp run`         (default) — start the MCP server.
* `gmc-mcp auth-init`   — interactive OAuth flow that produces a token JSON.
* `gmc-mcp version`     — print the package version.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from . import __version__
from ._logging import configure_default, get_logger
from .auth import SCOPES
from .config import load_config
from .server import build_server

logger = get_logger("cli")


@click.group(invoke_without_command=True)
@click.option(
    "--env",
    "env_file",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path to a .env file. Defaults to ./.env.",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default=None,
    help="Override GMC_TRANSPORT.",
)
@click.option(
    "--host",
    default=None,
    help="Bind host for SSE (default 127.0.0.1).",
)
@click.option(
    "--port",
    type=int,
    default=None,
    help="Bind port for SSE (default 8000).",
)
@click.pass_context
def cli(
    ctx: click.Context,
    env_file: Path | None,
    transport: str | None,
    host: str | None,
    port: int | None,
) -> None:
    """Google Merchant Center MCP server."""
    ctx.ensure_object(dict)
    ctx.obj["env_file"] = env_file
    ctx.obj["transport"] = transport
    ctx.obj["host"] = host
    ctx.obj["port"] = port
    if ctx.invoked_subcommand is None:
        ctx.invoke(run)


@cli.command()
@click.pass_context
def run(ctx: click.Context) -> None:
    """Start the MCP server (default subcommand)."""
    configure_default()
    env_file = ctx.obj.get("env_file")
    config = load_config(env_file=env_file)
    if ctx.obj.get("transport"):
        config.transport = ctx.obj["transport"]
    if ctx.obj.get("host"):
        config.host = ctx.obj["host"]
    if ctx.obj.get("port"):
        config.port = ctx.obj["port"]

    mcp = build_server(config=config)

    if config.transport == "stdio":
        mcp.run("stdio")
    elif config.transport == "sse":
        mcp.settings.host = config.host
        mcp.settings.port = config.port
        mcp.run("sse")
    else:
        raise click.ClickException(f"Unknown transport: {config.transport}")


@cli.command("auth-init")
@click.option(
    "--client-secrets",
    "secrets_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to the OAuth client_secret JSON downloaded from GCP.",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("secrets/oauth-token.json"),
    help="Where to save the resulting token (default: secrets/oauth-token.json).",
)
@click.option(
    "--port",
    type=int,
    default=0,
    help="Local callback port for the OAuth redirect. 0 picks an unused port.",
)
def auth_init(secrets_path: Path, output_path: Path, port: int) -> None:
    """Run a one-time interactive OAuth flow and save the resulting token JSON."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as e:  # pragma: no cover
        raise click.ClickException(
            "google-auth-oauthlib is required for auth-init. "
            "Install it with: pip install gmc-mcp[oauth]"
        ) from e

    flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
    creds = flow.run_local_server(port=port, prompt="consent")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(creds.to_json(), encoding="utf-8")
    click.echo(f"Saved token to {output_path}")
    click.echo(
        "Set this in your .env: "
        f"GMC_OAUTH_TOKEN={output_path.resolve()}"
    )


@cli.command()
@click.option("--host", default="127.0.0.1", help="Bind host.")
@click.option("--port", type=int, default=8765, help="Bind port.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="If set, append every received notification to this JSONL file.",
)
def webhook(host: str, port: int, out_path: Path | None) -> None:
    """Run a tiny HTTP server that decodes Pub/Sub push notifications from
    Merchant Center and prints / logs them.

    Use this as the callback URI when calling gmc_subscribe.

    Wire to a public HTTPS URL via Cloudflare Tunnel / ngrok in production.
    """
    import base64
    import json as _json
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    configure_default()
    log = get_logger("webhook")

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b""
            try:
                envelope = _json.loads(raw.decode("utf-8"))
                msg = envelope.get("message", {})
                data_b64 = msg.get("data", "")
                decoded: Any = None
                if data_b64:
                    try:
                        decoded = _json.loads(base64.b64decode(data_b64).decode("utf-8"))
                    except Exception:
                        decoded = base64.b64decode(data_b64).decode("utf-8", errors="replace")
                event = {
                    "subscription": envelope.get("subscription"),
                    "messageId": msg.get("messageId"),
                    "publishTime": msg.get("publishTime"),
                    "attributes": msg.get("attributes"),
                    "data": decoded,
                }
                log.info("webhook event: %s", _json.dumps(event)[:500])
                if out_path:
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    with out_path.open("a", encoding="utf-8") as f:
                        f.write(_json.dumps(event, ensure_ascii=False) + "\n")
            except Exception as e:  # pragma: no cover
                log.error("failed to parse webhook: %s", e)
            self.send_response(204)
            self.end_headers()

        def log_message(self, *args: Any, **kwargs: Any) -> None:  # quiet base logger
            pass

    server = ThreadingHTTPServer((host, port), Handler)
    log.info("webhook listening on http://%s:%d/", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("webhook stopped")


@cli.command("register-gcp")
@click.option(
    "--developer-email",
    default=None,
    help="Email Google will use for critical service announcements (optional).",
)
@click.pass_context
def register_gcp(ctx: click.Context, developer_email: str | None) -> None:
    """One-time link of your GCP project to your Merchant Center.

    Required before any v1 Merchant API call works for a new project.
    Idempotent: safe to run again — Google returns the existing registration.
    """
    from .audit import AuditLog
    from .auth import load_auth
    from .client import MerchantClient

    configure_default()
    config = load_config(env_file=ctx.obj.get("env_file"))
    auth = load_auth(
        service_account_key=config.service_account_key,
        oauth_token=config.oauth_token,
    )
    audit = AuditLog(config.audit_log)
    body: dict = {}
    if developer_email:
        body["developerEmail"] = developer_email
    with MerchantClient(config, auth, audit) as client:
        out = client.request(
            "POST",
            f"accounts/v1/{client.account_path()}/developerRegistration:registerGcp",
            json_body=body,
            op="register_gcp",
        )
    click.echo(json.dumps(out, indent=2, ensure_ascii=False))


@cli.command()
def version() -> None:
    """Print the gmc-mcp version."""
    click.echo(__version__)


@cli.command("describe")
@click.pass_context
def describe(ctx: click.Context) -> None:
    """Print effective config (auth, account, paths) and exit. Useful for debugging."""
    configure_default()
    env_file = ctx.obj.get("env_file")
    config = load_config(env_file=env_file)
    info = {
        "version": __version__,
        "account_id": config.account_id,
        "subaccount_id": config.subaccount_id,
        "service_account_key": str(config.service_account_key) if config.service_account_key else None,
        "oauth_token": str(config.oauth_token) if config.oauth_token else None,
        "audit_log": str(config.audit_log),
        "dry_run": config.dry_run,
        "transport": config.transport,
        "host": config.host,
        "port": config.port,
    }
    click.echo(json.dumps(info, indent=2, ensure_ascii=False))


def main() -> None:
    try:
        cli(obj={})
    except RuntimeError as e:
        # Surface config errors cleanly instead of a Python traceback.
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
