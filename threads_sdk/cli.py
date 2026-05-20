"""CLI interface for threads-sdk."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from threads_sdk.auth import Auth, Credentials
from threads_sdk.client import ThreadsClient
from threads_sdk.exceptions import ThreadsError

console = Console()
CREDENTIALS_PATH = Path.home() / ".threads-sdk" / "credentials.json"


def _load_client() -> ThreadsClient:
    """Load credentials and create client."""
    try:
        creds = Credentials.load(CREDENTIALS_PATH)
    except FileNotFoundError:
        console.print("[red]No credentials found. Run 'threads-sdk auth' first.[/red]")
        sys.exit(1)
    return ThreadsClient(credentials=creds)


@click.group()
def main() -> None:
    """threads-sdk - Modern CLI for Meta's Threads API."""
    pass


@main.command()
@click.option("--client-id", prompt="Client ID", help="Meta App Client ID")
@click.option("--client-secret", prompt="Client Secret", help="Meta App Client Secret")
@click.option("--redirect-uri", default="https://localhost", help="OAuth redirect URI")
def auth(client_id: str, client_secret: str, redirect_uri: str) -> None:
    """Set up OAuth authentication."""
    auth_handler = Auth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )
    url = auth_handler.get_authorization_url()
    console.print(f"\n[bold]Open this URL in your browser:[/bold]\n{url}\n")
    console.print("[dim]After authorizing, copy the 'code' parameter from the redirect URL.[/dim]")
    code = click.prompt("Enter the authorization code")

    creds = auth_handler.exchange_code(code)

    # Exchange for long-lived token
    long_token = auth_handler.get_long_lived_token(creds.access_token)
    creds.access_token = long_token.access_token
    creds.expires_at = __import__("time").time() + long_token.expires_in

    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    creds.save(CREDENTIALS_PATH)
    console.print(f"\n[green]Credentials saved to {CREDENTIALS_PATH}[/green]")
    console.print(f"[dim]Token expires in {long_token.expires_in // 86400} days[/dim]")


@main.command()
@click.argument("text")
@click.option("--image", default=None, help="Image URL to attach")
@click.option("--video", default=None, help="Video URL to attach")
def post(text: str, image: Optional[str], video: Optional[str]) -> None:
    """Publish a new post."""
    client = _load_client()
    with client:
        if image:
            result = client.create_image_post(image, text)
        elif video:
            result = client.create_video_post(video, text)
        else:
            result = client.create_text_post(text)
        console.print(f"[green]Post published![/green] ID: {result.id}")
        if result.permalink:
            console.print(f"Link: {result.permalink}")


@main.command()
@click.option("--limit", default=10, help="Number of posts to show")
def posts(limit: int) -> None:
    """List your recent posts."""
    client = _load_client()
    with client:
        user_posts = client.get_user_posts(limit=limit)
        if not user_posts:
            console.print("[dim]No posts found.[/dim]")
            return
        table = Table(title="Your Posts")
        table.add_column("ID", style="cyan")
        table.add_column("Text", max_width=50)
        table.add_column("Type")
        table.add_column("Timestamp")
        for p in user_posts:
            table.add_row(p.id, p.text[:50] if p.text else "", p.media_type, p.timestamp)
        console.print(table)


@main.command()
@click.argument("post_id")
def replies(post_id: str) -> None:
    """List replies to a post."""
    client = _load_client()
    with client:
        reply_list = client.get_post_replies(post_id)
        if not reply_list:
            console.print("[dim]No replies found.[/dim]")
            return
        table = Table(title=f"Replies to {post_id}")
        table.add_column("ID", style="cyan")
        table.add_column("User")
        table.add_column("Text", max_width=50)
        for r in reply_list:
            table.add_row(r.id, r.username, r.text[:50] if r.text else "")
        console.print(table)


@main.command()
@click.argument("post_id")
def insights(post_id: str) -> None:
    """Show insights for a post."""
    client = _load_client()
    with client:
        data = client.get_post_insights(post_id)
        table = Table(title=f"Insights for {post_id}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        table.add_row("Views", str(data.views))
        table.add_row("Likes", str(data.likes))
        table.add_row("Replies", str(data.replies))
        table.add_row("Reposts", str(data.reposts))
        table.add_row("Quotes", str(data.quotes))
        console.print(table)


@main.command()
@click.argument("post_id")
@click.argument("text")
def reply(post_id: str, text: str) -> None:
    """Reply to a post."""
    client = _load_client()
    with client:
        result = client.reply_to_post(post_id, text)
        console.print(f"[green]Reply published![/green] ID: {result.id}")
