"""
CLI entry point — run the server or interact via console.
"""

import argparse
import asyncio
import sys

import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()


def run_server():
    """Start the FastAPI server."""
    from app.config import get_settings
    settings = get_settings()

    console.print(Panel(
        f"[bold green]🚀 {settings.app_name} v1.0.0[/bold green]\n"
        f"Environment: {settings.app_env}\n"
        f"Telegram Mode: {settings.telegram_mode}\n"
        f"Database: {settings.database_url}\n"
        f"Dashboard: http://localhost:{settings.app_port}/dashboard\n"
        f"API Docs: http://localhost:{settings.app_port}/docs",
        title="TaskPilot Server",
        border_style="cyan",
    ))

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
    )


async def run_console():
    """Interactive console mode for testing without WhatsApp."""
    from app.core.database import async_session_factory, init_db
    from app.core.logging import setup_logging
    from app.services.orchestrator import OrchestrationService

    setup_logging()
    await init_db()

    console.print(Panel(
        "[bold cyan]🚀 TaskPilot Console Mode[/bold cyan]\n\n"
        "Chat with the AI task scheduler directly.\n"
        "Type 'quit' to exit.\n"
        "Type 'help' for commands.",
        border_style="cyan",
    ))

    chat_id = "999999999"

    while True:
        try:
            message = Prompt.ask("\n[bold green]You[/bold green]")
            if message.lower() in ("quit", "exit", "q"):
                console.print("[yellow]Goodbye! Keep crushing your tasks! 🚀[/yellow]")
                break

            async with async_session_factory() as db:
                service = OrchestrationService(db)
                response = await service.handle_incoming_message(chat_id, message)
                await db.commit()
                console.print(Panel(response, title="TaskPilot Reply", border_style="green"))

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def main():
    parser = argparse.ArgumentParser(description="TaskPilot — AI Task Scheduler")
    parser.add_argument(
        "mode",
        choices=["server", "console"],
        default="server",
        nargs="?",
        help="Run mode: 'server' for HTTP API, 'console' for interactive chat",
    )
    args = parser.parse_args()

    if args.mode == "console":
        asyncio.run(run_console())
    else:
        run_server()


if __name__ == "__main__":
    main()
