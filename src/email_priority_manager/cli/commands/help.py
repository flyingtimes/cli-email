"""
Help Command Implementation

This module provides the help command for the Email Priority Manager CLI.
"""

import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..framework.help import get_help_system, show_help_overview, show_topic_help, show_command_help, search_help
from ..utils.colors import Colors, StyledOutput
from ..base import with_context, CommandContext


console = Console()


@click.command(
    name="help",
    help="Show help information and documentation"
)
@click.argument(
    "topic",
    required=False,
    default=None
)
@click.option(
    "--search",
    "-s",
    help="Search help topics"
)
@click.option(
    "--list-topics",
    is_flag=True,
    help="List all available help topics"
)
@click.option(
    "--list-commands",
    is_flag=True,
    help="List all available commands"
)
@click.option(
    "--format",
    type=click.Choice(["text", "markdown"]),
    default="text",
    help="Output format for help content"
)
@with_context
def help_command(
    cmd_ctx: CommandContext,
    topic: Optional[str],
    search: Optional[str],
    list_topics: bool,
    list_commands: bool,
    format: str
):
    """
    Show comprehensive help information for the Email Priority Manager.

    Use this command to get help on specific topics, search for information,
    or browse the complete help system.
    """
    help_system = get_help_system()

    try:
        if search:
            # Search functionality
            results = search_help(search)
            if results:
                cmd_ctx.success(f"Found {len(results)} results for '{search}':")
                console.print()

                for result in results:
                    result_type, result_id = result.split(":", 1)
                    if result_type == "topic":
                        topic = help_system.topics.get(result_id)
                        if topic:
                            console.print(f"  • {Colors.CYAN}{topic.title}{Colors.RESET} ({Colors.GRAY}{result_id}{Colors.RESET})")
                            console.print(f"    {topic.description[:80]}...")
                    elif result_type == "command":
                        command = help_system.commands.get(result_id)
                        if command:
                            console.print(f"  • {Colors.GREEN}{command.name}{Colors.RESET} ({Colors.GRAY}{result_id}{Colors.RESET})")
                            console.print(f"    {command.description[:80]}...")

                console.print()
                cmd_ctx.info("Use 'email-priority-manager help <topic|command>' for detailed information.")
            else:
                cmd_ctx.warning(f"No results found for '{search}'")
                cmd_ctx.info("Use --list-topics to see available topics.")

        elif list_topics:
            # List all topics
            help_system.show_all_topics()

        elif list_commands:
            # List all commands
            help_system.show_all_commands()

        elif topic:
            # Show specific topic or command help
            if topic in help_system.topics:
                show_topic_help(topic)
            elif topic in help_system.commands:
                show_command_help(topic)
            else:
                # Try to find partial matches
                topic_matches = [tid for tid in help_system.topics.keys() if topic in tid]
                command_matches = [cid for cid in help_system.commands.keys() if topic in cid]

                if topic_matches or command_matches:
                    cmd_ctx.warning(f"Topic '{topic}' not found. Did you mean:")
                    if topic_matches:
                        cmd_ctx.info("Topics:")
                        for match in topic_matches:
                            cmd_ctx.info(f"  • {match}")
                    if command_matches:
                        cmd_ctx.info("Commands:")
                        for match in command_matches:
                            cmd_ctx.info(f"  • {match}")
                else:
                    cmd_ctx.error(f"Topic '{topic}' not found")
                    cmd_ctx.info("Use --list-topics to see available topics.")
                    sys.exit(1)

        else:
            # Show main help overview
            show_help_overview()

    except Exception as e:
        cmd_ctx.error(f"Error displaying help: {str(e)}")
        if cmd_ctx.verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


# Register help command
def register_help_command(cli_group):
    """Register the help command with the CLI group."""
    cli_group.add_command(help_command)


# Add command help information
def setup_command_help():
    """Set up help information for built-in commands."""
    help_system = get_help_system()

    # Add help for main CLI
    help_system.add_command_help(
        "main",
        CommandHelp(
            name="email-priority-manager",
            description="Main CLI entry point for email management",
            usage="email-priority-manager [OPTIONS] COMMAND [ARGS]",
            options=[
                {
                    "option": "--verbose, -v",
                    "description": "Enable verbose output"
                },
                {
                    "option": "--quiet, -q",
                    "description": "Suppress all output except errors"
                },
                {
                    "option": "--config-file FILE",
                    "description": "Path to configuration file"
                },
                {
                    "option": "--log-level LEVEL",
                    "description": "Set logging level (DEBUG, INFO, WARNING, ERROR)"
                },
                {
                    "option": "--help, -h",
                    "description": "Show help message"
                }
            ],
            examples=[
                "email-priority-manager --verbose",
                "email-priority-manager --config-file custom-config.yaml scan",
                "email-priority-manager --log-level DEBUG classify"
            ],
            notes=[
                "Use --help after any command to see command-specific help",
                "Configuration file is optional - system will use defaults if not provided",
                "Log levels control verbosity of output during operations"
            ],
            category="main"
        )
    )

    # Add help for help command itself
    help_system.add_command_help(
        "help",
        CommandHelp(
            name="help",
            description="Show help information and documentation",
            usage="email-priority-manager help [TOPIC] [OPTIONS]",
            options=[
                {
                    "option": "--search, -s TEXT",
                    "description": "Search help topics"
                },
                {
                    "option": "--list-topics",
                    "description": "List all available help topics"
                },
                {
                    "option": "--list-commands",
                    "description": "List all available commands"
                },
                {
                    "option": "--format FORMAT",
                    "description": "Output format (text, markdown)"
                }
            ],
            examples=[
                "email-priority-manager help",
                "email-priority-manager help getting-started",
                "email-priority-manager help --search classification",
                "email-priority-manager help --list-topics"
            ],
            notes=[
                "Help topics cover concepts, features, and troubleshooting",
                "Use --search to find relevant help content quickly",
                "Command help shows usage examples and options"
            ],
            category="help"
        )
    )