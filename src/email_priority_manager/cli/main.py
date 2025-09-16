"""
Main CLI Entry Point

This module provides the main entry point for the Email Priority Manager CLI application.
It uses Click as the CLI framework and provides a robust command structure with
comprehensive help system and extensible architecture.
"""

import sys
import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .framework.setup import setup_cli_framework
from .utils.colors import Colors
from .utils.logging import setup_cli_logging
from .utils.prompts import confirm_action
from .commands.help import register_help_command, setup_command_help


# Initialize rich console for enhanced output
console = Console()


# Main CLI group
@click.group(
    name="email-priority-manager",
    help="Email Priority Manager - Intelligent email classification and organization tool",
    context_settings={"help_option_names": ["-h", "--help"]}
)
@click.version_option(
    version="0.1.0",
    prog_name="Email Priority Manager",
    message="%(prog)s version %(version)s"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output"
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Suppress all output except errors"
)
@click.option(
    "--config-file",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to configuration file"
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Set logging level"
)
@click.pass_context
def cli(ctx, verbose, quiet, config_file, log_level):
    """
    Email Priority Manager - Intelligent email classification and organization tool

    This CLI provides comprehensive tools for managing your emails with AI-powered
    classification, priority assessment, and organization capabilities.
    """
    # Set up context for command execution
    ctx.ensure_object(dict)

    # Store CLI options in context
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["config_file"] = config_file
    ctx.obj["log_level"] = log_level

    # Set up logging
    if quiet:
        ctx.obj["log_level"] = "ERROR"
    elif verbose:
        ctx.obj["log_level"] = "DEBUG"

    # Initialize CLI framework
    setup_cli_framework(ctx.obj)

    # Set up logging
    setup_cli_logging(ctx.obj["log_level"])

    # Display welcome message if no command provided
    if len(sys.argv) == 1:
        display_welcome_message()


def display_welcome_message():
    """Display welcome message and basic usage information."""
    welcome_text = Text()
    welcome_text.append("Welcome to ", style="bold blue")
    welcome_text.append("Email Priority Manager", style="bold green")
    welcome_text.append("!", style="bold blue")

    panel = Panel(
        welcome_text,
        title="Email Priority Manager v0.1.0",
        border_style="blue",
        padding=(1, 2)
    )

    console.print(panel)
    console.print()

    # Display quick start information
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Command", style="cyan", width=15)
    table.add_column("Description", style="white")

    table.add_row("init", "Initialize email database and configuration")
    table.add_row("scan", "Scan mailbox for emails")
    table.add_row("classify", "Process and classify emails")
    table.add_row("list", "Display emails with filters")
    table.add_row("tag", "Manage email tags")
    table.add_row("config", "Manage configuration")
    table.add_row("export", "Export email data")
    table.add_row("stats", "Show statistics and reports")

    console.print(table)
    console.print()
    console.print(f"{Colors.YELLOW}Use --help for detailed usage information{Colors.RESET}")


# Command groups for better organization
@cli.group(
    name="setup",
    help="Setup and configuration commands"
)
def setup_group():
    """Setup and configuration commands."""
    pass


@cli.group(
    name="email",
    help="Email processing and management commands"
)
def email_group():
    """Email processing and management commands."""
    pass


@cli.group(
    name="query",
    help="Query and display commands"
)
def query_group():
    """Query and display commands."""
    pass


@cli.group(
    name="data",
    help="Data management and export commands"
)
def data_group():
    """Data management and export commands."""
    pass


# Error handling and validation
def handle_cli_error(error, exit_code=1):
    """Handle CLI errors with user-friendly messages."""
    if isinstance(error, click.ClickException):
        console.print(f"{Colors.RED}Error: {error.message}{Colors.RESET}")
    else:
        console.print(f"{Colors.RED}Unexpected error: {str(error)}{Colors.RESET}")

    sys.exit(exit_code)


# Main entry point
# Set up help system
setup_command_help()
register_help_command(cli)


def main():
    """Main entry point for the CLI application."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        handle_cli_error(e)


if __name__ == "__main__":
    main()