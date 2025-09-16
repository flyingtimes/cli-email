"""
CLI Logging Utilities

This module provides logging configuration and utilities for CLI operations.
"""

import logging
import sys
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from .colors import Colors, ColorScheme


class CLIFormatter(logging.Formatter):
    """Custom formatter for CLI output with colors."""

    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors and Colors.supports_color()
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        level_name = record.levelname
        message = record.getMessage()

        if self.use_colors:
            # Apply colors based on log level
            if record.levelno >= logging.ERROR:
                level_name = Colors.colorize(level_name, Colors.RED)
                message = Colors.colorize(message, Colors.RED)
            elif record.levelno >= logging.WARNING:
                level_name = Colors.colorize(level_name, Colors.YELLOW)
                message = Colors.colorize(message, Colors.YELLOW)
            elif record.levelno >= logging.INFO:
                level_name = Colors.colorize(level_name, Colors.BLUE)
                message = Colors.colorize(message, Colors.BLUE)
            else:  # DEBUG
                level_name = Colors.colorize(level_name, Colors.GRAY)
                message = Colors.colorize(message, Colors.GRAY)

        # Include timestamp and module info if available
        if hasattr(record, 'name') and record.name != 'root':
            return f"[{recordasctime}] {level_name} [{record.name}] {message}"
        else:
            return f"[{recordasctime}] {level_name} {message}"

    def formatTime(self, record, datefmt=None):
        """Format time for log record."""
        if datefmt:
            return datetime.fromtimestamp(record.created).strftime(datefmt)
        return datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")


class CLILogger:
    """CLI-specific logger with enhanced features."""

    def __init__(self, name: str = "email_priority_manager"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self._configured = False

    def setup(
        self,
        level: str = "INFO",
        console_output: bool = True,
        file_output: bool = False,
        log_file: Optional[str] = None,
        use_colors: bool = True
    ):
        """Set up logging configuration."""
        if self._configured:
            return

        # Clear existing handlers
        self.logger.handlers.clear()

        # Set logging level
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(log_level)

        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_formatter = CLIFormatter(use_colors=use_colors)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # File handler
        if file_output:
            if log_file is None:
                log_dir = Path.home() / ".email-priority-manager" / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                log_file = log_dir / f"epm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)  # File gets all logs
            file_formatter = CLIFormatter(use_colors=False)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

        self._configured = True

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, **kwargs)

    def success(self, message: str, **kwargs):
        """Log success message."""
        self.info(f"SUCCESS: {message}", **kwargs)

    def command_start(self, command: str, **kwargs):
        """Log command start."""
        self.info(f"Command started: {command}", **kwargs)

    def command_complete(self, command: str, duration: Optional[float] = None, **kwargs):
        """Log command completion."""
        if duration:
            self.info(f"Command completed: {command} (took {duration:.2f}s)", **kwargs)
        else:
            self.info(f"Command completed: {command}", **kwargs)

    def command_error(self, command: str, error: str, **kwargs):
        """Log command error."""
        self.error(f"Command failed: {command} - {error}", **kwargs)


def setup_cli_logging(
    level: str = "INFO",
    console_output: bool = True,
    file_output: bool = False,
    log_file: Optional[str] = None,
    use_colors: bool = True
) -> CLILogger:
    """Set up CLI logging with sensible defaults."""
    logger = CLILogger()
    logger.setup(
        level=level,
        console_output=console_output,
        file_output=file_output,
        log_file=log_file,
        use_colors=use_colors
    )
    return logger


def get_logger(name: str = "email_priority_manager") -> CLILogger:
    """Get logger instance."""
    return CLILogger(name)


class LogContext:
    """Context manager for logging with timing."""

    def __init__(self, logger: CLILogger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None

    def __enter__(self):
        """Enter context, start timing."""
        self.start_time = datetime.now()
        self.logger.info(f"Starting {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context, log completion."""
        duration = (datetime.now() - self.start_time).total_seconds()

        if exc_type:
            self.logger.error(f"Failed {self.operation} after {duration:.2f}s: {exc_val}")
        else:
            self.logger.info(f"Completed {self.operation} in {duration:.2f}s")


class ProgressLogger:
    """Logger for progress tracking."""

    def __init__(self, logger: CLILogger, total: int, operation: str = "Processing"):
        self.logger = logger
        self.total = total
        self.operation = operation
        self.current = 0
        self.last_percentage = -1
        self.start_time = datetime.now()

    def update(self, advance: int = 1):
        """Update progress."""
        self.current += advance
        percentage = int((self.current / self.total) * 100)

        # Log at specific intervals
        if percentage != self.last_percentage and percentage % 10 == 0:
            self.last_percentage = percentage
            self.logger.info(f"{self.operation}: {percentage}% complete ({self.current}/{self.total})")

    def complete(self):
        """Mark as complete."""
        duration = (datetime.now() - self.start_time).total_seconds()
        self.logger.success(f"{self.operation} completed {self.current} items in {duration:.2f}s")


def log_function_call(func):
    """Decorator to log function calls."""
    def wrapper(*args, **kwargs):
        logger = get_logger()
        func_name = func.__name__

        with LogContext(logger, f"function call: {func_name}"):
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Function {func_name} returned successfully")
                return result
            except Exception as e:
                logger.error(f"Function {func_name} failed: {str(e)}")
                raise

    return wrapper


def log_command_execution(command_name: str):
    """Decorator to log command execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger()

            logger.command_start(command_name)
            start_time = datetime.now()

            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.command_complete(command_name, duration)
                return result
            except Exception as e:
                logger.command_error(command_name, str(e))
                raise

        return wrapper
    return decorator


class PerformanceLogger:
    """Logger for performance metrics."""

    def __init__(self, logger: CLILogger):
        self.logger = logger
        self.metrics = {}

    def start_timing(self, operation: str):
        """Start timing an operation."""
        self.metrics[operation] = {
            'start_time': datetime.now(),
            'end_time': None,
            'duration': None
        }

    def end_timing(self, operation: str):
        """End timing an operation."""
        if operation in self.metrics:
            self.metrics[operation]['end_time'] = datetime.now()
            self.metrics[operation]['duration'] = (
                self.metrics[operation]['end_time'] -
                self.metrics[operation]['start_time']
            ).total_seconds()

            duration = self.metrics[operation]['duration']
            self.logger.info(f"Performance: {operation} took {duration:.3f}s")

    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        return self.metrics.copy()

    def reset_metrics(self):
        """Reset all metrics."""
        self.metrics.clear()


# Global logger instance
_global_logger = None


def get_global_logger() -> CLILogger:
    """Get global logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = setup_cli_logging()
    return _global_logger


def set_global_logger(logger: CLILogger):
    """Set global logger instance."""
    global _global_logger
    _global_logger = logger