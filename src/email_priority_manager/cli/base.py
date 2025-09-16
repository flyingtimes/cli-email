"""
Base Command Framework

This module provides the base command framework with common functionality,
validation, and utilities for all CLI commands.
"""

import sys
import os
from typing import Any, Dict, Optional, List, Callable
from functools import wraps
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from .utils.colors import Colors
from .utils.logging import get_logger
from .progress import create_progress_indicator


# Initialize console and logger
console = Console()
logger = get_logger(__name__)


class CLIError(Exception):
    """Base exception for CLI-related errors."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


class ValidationError(CLIError):
    """Raised when validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message, exit_code=2)


class CommandContext:
    """Context object for command execution."""

    def __init__(self, ctx: click.Context):
        self.ctx = ctx
        self.verbose = ctx.obj.get("verbose", False)
        self.quiet = ctx.obj.get("quiet", False)
        self.config_file = ctx.obj.get("config_file")
        self.log_level = ctx.obj.get("log_level", "INFO")

    def log(self, message: str, level: str = "INFO"):
        """Log a message if not in quiet mode."""
        if not self.quiet:
            if level == "DEBUG" and self.verbose:
                console.print(f"{Colors.GRAY}[DEBUG] {message}{Colors.RESET}")
            elif level == "INFO":
                console.print(f"{Colors.BLUE}[INFO] {message}{Colors.RESET}")
            elif level == "WARNING":
                console.print(f"{Colors.YELLOW}[WARNING] {message}{Colors.RESET}")
            elif level == "ERROR":
                console.print(f"{Colors.RED}[ERROR] {message}{Colors.RESET}")

    def success(self, message: str):
        """Display success message."""
        if not self.quiet:
            console.print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

    def error(self, message: str):
        """Display error message."""
        console.print(f"{Colors.RED}✗ {message}{Colors.RESET}")

    def debug(self, message: str):
        """Display debug message."""
        if self.verbose and not self.quiet:
            console.print(f"{Colors.GRAY}[DEBUG] {message}{Colors.RESET}")


class BaseCommand:
    """Base class for all CLI commands."""

    def __init__(self, name: str, help_text: str = ""):
        self.name = name
        self.help_text = help_text
        self.validators: List[Callable] = []

    def add_validator(self, validator: Callable):
        """Add a validator function to the command."""
        self.validators.append(validator)

    def validate(self, context: CommandContext, **kwargs) -> bool:
        """Run all validators for the command."""
        for validator in self.validators:
            try:
                validator(context, **kwargs)
            except ValidationError as e:
                context.error(f"Validation failed: {e.message}")
                return False
        return True

    def execute(self, context: CommandContext, **kwargs) -> Any:
        """Execute the command. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement execute method")

    def handle_error(self, error: Exception, context: CommandContext):
        """Handle errors during command execution."""
        if isinstance(error, CLIError):
            context.error(error.message)
        else:
            context.error(f"Unexpected error: {str(error)}")
            if context.verbose:
                import traceback
                console.print(traceback.format_exc())


def with_context(func):
    """Decorator to provide command context to command functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract click context from arguments
        ctx = None
        for arg in args:
            if isinstance(arg, click.Context):
                ctx = arg
                break

        if ctx is None:
            raise CLIError("No click context found")

        # Create command context
        cmd_ctx = CommandContext(ctx)

        try:
            return func(cmd_ctx, *args, **kwargs)
        except Exception as e:
            cmd_ctx.handle_error(e, cmd_ctx)
            sys.exit(1)

    return wrapper


def with_progress(description: str = "Processing...", total: Optional[int] = None):
    """Decorator to add progress indication to command functions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cmd_ctx = None
            for arg in args:
                if isinstance(arg, CommandContext):
                    cmd_ctx = arg
                    break

            if cmd_ctx is None:
                return func(*args, **kwargs)

            # Create progress indicator
            progress = create_progress_indicator(description, total=total)

            try:
                with progress:
                    # Add progress to command context
                    cmd_ctx.progress = progress
                    result = func(*args, **kwargs)
                    return result
            except Exception as e:
                if hasattr(cmd_ctx, 'progress'):
                    cmd_ctx.progress.console.print(f"\n{Colors.RED}Error: {str(e)}{Colors.RESET}")
                raise

        return wrapper
    return decorator


def validate_email_ids(email_ids: List[str]) -> bool:
    """Validate email ID format."""
    if not email_ids:
        return True

    for email_id in email_ids:
        if not email_id.isdigit():
            raise ValidationError(f"Invalid email ID format: {email_id}", "email_ids")

    return True


def validate_date_format(date_str: str) -> bool:
    """Validate date format (YYYY-MM-DD or ISO format)."""
    from datetime import datetime

    if not date_str:
        return True

    try:
        datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return True
    except ValueError:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            raise ValidationError(f"Invalid date format: {date_str}", "date")


def validate_file_path(file_path: str, must_exist: bool = True, must_writable: bool = False) -> bool:
    """Validate file path."""
    if not file_path:
        return True

    from pathlib import Path

    path = Path(file_path)

    if must_exist and not path.exists():
        raise ValidationError(f"File does not exist: {file_path}", "file_path")

    if must_writable:
        parent = path.parent
        if not parent.exists():
            raise ValidationError(f"Parent directory does not exist: {parent}", "file_path")
        if not os.access(parent, os.W_OK):
            raise ValidationError(f"Parent directory is not writable: {parent}", "file_path")

    return True


def create_table(title: str = "", columns: Optional[List[str]] = None) -> Table:
    """Create a formatted table for output."""
    table = Table(
        title=title if title else None,
        show_header=True,
        header_style="bold magenta",
        border_style="blue"
    )

    if columns:
        for col in columns:
            table.add_column(col, style="white")

    return table


def display_table(table: Table, title: str = ""):
    """Display a formatted table."""
    if title:
        console.print(Panel(table, title=title, border_style="blue"))
    else:
        console.print(table)


def format_success_message(message: str) -> str:
    """Format a success message with color."""
    return f"{Colors.GREEN}✓ {message}{Colors.RESET}"


def format_error_message(message: str) -> str:
    """Format an error message with color."""
    return f"{Colors.RED}✗ {message}{Colors.RESET}"


def format_warning_message(message: str) -> str:
    """Format a warning message with color."""
    return f"{Colors.YELLOW}⚠ {message}{Colors.RESET}"


def format_info_message(message: str) -> str:
    """Format an info message with color."""
    return f"{Colors.BLUE}ℹ {message}{Colors.RESET}"


def require_config(func):
    """Decorator to require configuration for command execution."""
    @wraps(func)
    def wrapper(cmd_ctx: CommandContext, *args, **kwargs):
        if not cmd_ctx.config_file:
            cmd_ctx.error("Configuration file is required. Use --config-file option or run 'init' command first.")
            sys.exit(1)
        return func(cmd_ctx, *args, **kwargs)

    return wrapper


def handle_keyboard_interrupt(func):
    """Decorator to handle keyboard interrupts gracefully."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            console.print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
            sys.exit(130)

    return wrapper