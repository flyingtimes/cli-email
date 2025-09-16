"""
Color Management for CLI

This module provides color definitions and utilities for terminal output.
"""

import sys
from typing import Optional


class Colors:
    """Terminal color codes."""

    # Standard colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    HIDDEN = "\033[8m"

    # Reset
    RESET = "\033[0m"

    # Special
    GRAY = "\033[90m"

    @staticmethod
    def supports_color() -> bool:
        """Check if terminal supports color."""
        # Check if we're in a terminal
        if not sys.stdout.isatty():
            return False

        # Check for specific environment variables
        if os.environ.get('NO_COLOR'):
            return False

        # Check for common color support indicators
        term = os.environ.get('TERM', '').lower()
        if 'color' in term or 'ansi' in term or 'xterm' in term:
            return True

        # Windows 10+ supports ANSI colors
        if sys.platform == 'win32':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                return kernel32.GetConsoleMode(kernel32.GetStdHandle(-11)) & 0x0004
            except:
                pass

        return True

    @staticmethod
    def colorize(text: str, color: str) -> str:
        """Apply color to text."""
        if Colors.supports_color():
            return f"{color}{text}{Colors.RESET}"
        return text

    @staticmethod
    def red(text: str) -> str:
        """Make text red."""
        return Colors.colorize(text, Colors.RED)

    @staticmethod
    def green(text: str) -> str:
        """Make text green."""
        return Colors.colorize(text, Colors.GREEN)

    @staticmethod
    def yellow(text: str) -> str:
        """Make text yellow."""
        return Colors.colorize(text, Colors.YELLOW)

    @staticmethod
    def blue(text: str) -> str:
        """Make text blue."""
        return Colors.colorize(text, Colors.BLUE)

    @staticmethod
    def magenta(text: str) -> str:
        """Make text magenta."""
        return Colors.colorize(text, Colors.MAGENTA)

    @staticmethod
    def cyan(text: str) -> str:
        """Make text cyan."""
        return Colors.colorize(text, Colors.CYAN)

    @staticmethod
    def bold(text: str) -> str:
        """Make text bold."""
        return Colors.colorize(text, Colors.BOLD)

    @staticmethod
    def underline(text: str) -> str:
        """Make text underlined."""
        return Colors.colorize(text, Colors.UNDERLINE)

    @staticmethod
    def gray(text: str) -> str:
        """Make text gray."""
        return Colors.colorize(text, Colors.GRAY)

    @staticmethod
    def success(text: str) -> str:
        """Format text as success."""
        return Colors.colorize(f"✓ {text}", Colors.GREEN)

    @staticmethod
    def error(text: str) -> str:
        """Format text as error."""
        return Colors.colorize(f"✗ {text}", Colors.RED)

    @staticmethod
    def warning(text: str) -> str:
        """Format text as warning."""
        return Colors.colorize(f"⚠ {text}", Colors.YELLOW)

    @staticmethod
    def info(text: str) -> str:
        """Format text as info."""
        return Colors.colorize(f"ℹ {text}", Colors.BLUE)

    @staticmethod
    def highlight(text: str, color: str = Colors.YELLOW) -> str:
        """Highlight text with specified color."""
        return Colors.colorize(text, color)

    @staticmethod
    def progress_bar(percentage: float, width: int = 20, char: str = "█") -> str:
        """Create a text progress bar."""
        if percentage < 0:
            percentage = 0
        elif percentage > 100:
            percentage = 100

        filled = int(width * percentage / 100)
        bar = char * filled + " " * (width - filled)
        return f"[{bar}] {percentage:.1f}%"

    @staticmethod
    def status_badge(status: str, color: str = Colors.GREEN) -> str:
        """Create a status badge."""
        return Colors.colorize(f"[{status}]", color)


# Import os here to avoid circular imports
import os


class ColorScheme:
    """Color scheme definitions for different output types."""

    # Priority colors
    PRIORITY_URGENT = Colors.RED
    PRIORITY_HIGH = Colors.BRIGHT_RED
    PRIORITY_IMPORTANT = Colors.YELLOW
    PRIORITY_NORMAL = Colors.GREEN
    PRIORITY_LOW = Colors.BLUE

    # Status colors
    STATUS_SUCCESS = Colors.GREEN
    STATUS_ERROR = Colors.RED
    STATUS_WARNING = Colors.YELLOW
    STATUS_INFO = Colors.BLUE
    STATUS_PENDING = Colors.YELLOW
    STATUS_PROCESSING = Colors.CYAN
    STATUS_COMPLETED = Colors.GREEN
    STATUS_FAILED = Colors.RED

    # UI elements
    HEADER = Colors.BOLD + Colors.CYAN
    SUBHEADER = Colors.BOLD + Colors.BLUE
    EMPHASIS = Colors.BOLD + Colors.MAGENTA
    CODE = Colors.CYAN
    LINK = Colors.BLUE + Colors.UNDERLINE
    QUOTE = Colors.GRAY

    # Table colors
    TABLE_HEADER = Colors.BOLD + Colors.MAGENTA
    TABLE_BORDER = Colors.BLUE
    TABLE_ROW_EVEN = Colors.WHITE
    TABLE_ROW_ODD = Colors.GRAY

    # Progress colors
    PROGRESS_BAR = Colors.GREEN
    PROGRESS_BACKGROUND = Colors.GRAY
    PROGRESS_TEXT = Colors.WHITE

    # Error colors
    ERROR_MESSAGE = Colors.RED
    ERROR_BORDER = Colors.BRIGHT_RED
    ERROR_BACKGROUND = Colors.BG_RED

    # Success colors
    SUCCESS_MESSAGE = Colors.GREEN
    SUCCESS_BORDER = Colors.BRIGHT_GREEN
    SUCCESS_BACKGROUND = Colors.BG_GREEN

    # Warning colors
    WARNING_MESSAGE = Colors.YELLOW
    WARNING_BORDER = Colors.BRIGHT_YELLOW
    WARNING_BACKGROUND = Colors.BG_YELLOW

    @staticmethod
    def get_priority_color(priority: str) -> str:
        """Get color for priority level."""
        priority_colors = {
            'urgent': ColorScheme.PRIORITY_URGENT,
            'high': ColorScheme.PRIORITY_HIGH,
            'important': ColorScheme.PRIORITY_IMPORTANT,
            'normal': ColorScheme.PRIORITY_NORMAL,
            'low': ColorScheme.PRIORITY_LOW
        }
        return priority_colors.get(priority.lower(), ColorScheme.PRIORITY_NORMAL)

    @staticmethod
    def get_status_color(status: str) -> str:
        """Get color for status."""
        status_colors = {
            'success': ColorScheme.STATUS_SUCCESS,
            'error': ColorScheme.STATUS_ERROR,
            'warning': ColorScheme.STATUS_WARNING,
            'info': ColorScheme.STATUS_INFO,
            'pending': ColorScheme.STATUS_PENDING,
            'processing': ColorScheme.STATUS_PROCESSING,
            'completed': ColorScheme.STATUS_COMPLETED,
            'failed': ColorScheme.STATUS_FAILED
        }
        return status_colors.get(status.lower(), ColorScheme.STATUS_INFO)

    @staticmethod
    def format_priority(priority: str) -> str:
        """Format priority with appropriate color."""
        color = ColorScheme.get_priority_color(priority)
        return Colors.colorize(priority.upper(), color)

    @staticmethod
    def format_status(status: str) -> str:
        """Format status with appropriate color."""
        color = ColorScheme.get_status_color(status)
        return Colors.colorize(status.title(), color)


class StyledOutput:
    """Utility class for styled output."""

    @staticmethod
    def header(text: str, level: int = 1) -> str:
        """Format as header."""
        if level == 1:
            return Colors.colorize(f"=== {text.upper()} ===", ColorScheme.HEADER)
        elif level == 2:
            return Colors.colorize(f"--- {text.title()} ---", ColorScheme.SUBHEADER)
        else:
            return Colors.colorize(f"• {text}", ColorScheme.EMPHASIS)

    @staticmethod
    def success(message: str) -> str:
        """Format success message."""
        return Colors.colorize(f"✓ {message}", ColorScheme.SUCCESS_MESSAGE)

    @staticmethod
    def error(message: str) -> str:
        """Format error message."""
        return Colors.colorize(f"✗ {message}", ColorScheme.ERROR_MESSAGE)

    @staticmethod
    def warning(message: str) -> str:
        """Format warning message."""
        return Colors.colorize(f"⚠ {message}", ColorScheme.WARNING_MESSAGE)

    @staticmethod
    def info(message: str) -> str:
        """Format info message."""
        return Colors.colorize(f"ℹ {message}", ColorScheme.STATUS_INFO)

    @staticmethod
    def code(text: str) -> str:
        """Format as code."""
        return Colors.colorize(text, ColorScheme.CODE)

    @staticmethod
    def link(text: str, url: Optional[str] = None) -> str:
        """Format as link."""
        if url:
            return Colors.colorize(f"{text} ({url})", ColorScheme.LINK)
        return Colors.colorize(text, ColorScheme.LINK)

    @staticmethod
    def quote(text: str) -> str:
        """Format as quote."""
        return Colors.colorize(f'"{text}"', ColorScheme.QUOTE)

    @staticmethod
    def badge(text: str, color: str = ColorScheme.STATUS_INFO) -> str:
        """Format as badge."""
        return Colors.colorize(f"[{text}]", color)

    @staticmethod
    def progress_bar(percentage: float, width: int = 20) -> str:
        """Format progress bar."""
        if Colors.supports_color():
            bar = Colors.progress_bar(percentage, width)
            return Colors.colorize(bar, ColorScheme.PROGRESS_BAR)
        else:
            return f"Progress: {percentage:.1f}%"

    @staticmethod
    def table_cell(text: str, row_index: int = 0) -> str:
        """Format table cell."""
        if Colors.supports_color():
            color = ColorScheme.TABLE_ROW_EVEN if row_index % 2 == 0 else ColorScheme.TABLE_ROW_ODD
            return Colors.colorize(text, color)
        return text