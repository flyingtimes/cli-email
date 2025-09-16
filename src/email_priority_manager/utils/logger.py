"""
Logging configuration and utilities for Email Priority Manager.

Provides structured logging with configurable levels, formats, and outputs
including console, file, and rotation support.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache

from ..config.settings import get_settings


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }

    def format(self, record):
        """Format log record with colors."""
        if hasattr(record, 'levelname') and record.levelname in self.COLORS:
            # Add color to levelname
            original_levelname = record.levelname
            record.levelname = f"{self.COLORS[record.levelname]}{original_levelname}{self.COLORS['RESET']}"

        formatted = super().format(record)

        # Restore original levelname
        if hasattr(record, 'levelname'):
            record.levelname = original_levelname.split()[-1]  # Remove color codes

        return formatted


class StructuredFormatter(logging.Formatter):
    """Structured JSON-like log formatter."""

    def format(self, record):
        """Format log record as structured data."""
        log_data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra') and isinstance(record.extra, dict):
            log_data.update(record.extra)

        return self._to_json(log_data)

    def _to_json(self, data: Dict[str, Any]) -> str:
        """Convert data to JSON string."""
        try:
            import json
            return json.dumps(data, ensure_ascii=False, default=str)
        except ImportError:
            # Fallback to simple string representation
            return str(data)


@lru_cache()
def get_logger(name: str) -> logging.Logger:
    """Get logger instance with configuration."""
    return setup_logger(name)


def setup_logger(name: str, settings: Optional[Any] = None) -> logging.Logger:
    """Set up logger with configuration."""
    if settings is None:
        try:
            settings = get_settings()
        except Exception:
            # Use default settings if configuration not available
            settings = type('Settings', (), {
                'logging': type('Logging', (), {
                    'level': 'INFO',
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'file_path': None,
                    'max_file_size': 10485760,
                    'backup_count': 5
                })()
            })()

    logger = logging.getLogger(name)

    # Clear existing handlers
    logger.handlers.clear()

    # Set log level
    level = getattr(logging, settings.logging.level.upper(), logging.INFO)
    logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Use colored formatter for console
    console_formatter = ColoredFormatter(settings.logging.format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if configured)
    if settings.logging.file_path:
        try:
            log_file = Path(settings.logging.file_path)
            log_file.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=settings.logging.max_file_size,
                backupCount=settings.logging.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)

            # Use standard formatter for file
            file_formatter = logging.Formatter(settings.logging.format)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        except Exception as e:
            # Don't fail if file logging can't be set up
            console_handler.error(f"Failed to set up file logging: {e}")

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def configure_logging(settings: Optional[Any] = None):
    """Configure logging for the entire application."""
    # Clear existing loggers
    for logger_name in logging.root.manager.loggerDict:
        if logger_name.startswith('email_priority_manager'):
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    if settings is None:
        try:
            settings = get_settings()
        except Exception:
            settings = type('Settings', (), {
                'logging': type('Logging', (), {
                    'level': 'INFO',
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'file_path': None,
                    'max_file_size': 10485760,
                    'backup_count': 5
                })()
            })()

    # Configure root logger
    level = getattr(logging, settings.logging.level.upper(), logging.INFO)
    root_logger.setLevel(level)

    # Console handler for root
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = ColoredFormatter(settings.logging.format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler for root (if configured)
    if settings.logging.file_path:
        try:
            log_file = Path(settings.logging.file_path)
            log_file.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=settings.logging.max_file_size,
                backupCount=settings.logging.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(settings.logging.format)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

        except Exception as e:
            console_handler.error(f"Failed to set up file logging: {e}")

    # Configure third-party library loggers
    third_party_loggers = [
        'sqlalchemy',
        'urllib3',
        'requests',
        'openai',
        'asyncio'
    ]

    for logger_name in third_party_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)  # Less verbose for third-party libs
        logger.propagate = True


class LoggerMixin:
    """Mixin class to add logging capability to any class."""

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return get_logger(self.__class__.__name__)


def log_function_call(func):
    """Decorator to log function calls."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__}", extra={
            'function': func.__name__,
            'args_count': len(args),
            'kwargs_count': len(kwargs)
        })

        try:
            result = func(*args, **kwargs)
            logger.debug(f"Completed {func.__name__}", extra={
                'function': func.__name__,
                'success': True
            })
            return result

        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", extra={
                'function': func.__name__,
                'error': str(e),
                'success': False
            })
            raise

    return wrapper


def log_performance(threshold_ms: int = 100):
    """Decorator to log function performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                logger = get_logger(func.__module__)

                if duration_ms > threshold_ms:
                    logger.warning(f"Slow function {func.__name__}", extra={
                        'function': func.__name__,
                        'duration_ms': duration_ms,
                        'threshold_ms': threshold_ms
                    })
                else:
                    logger.debug(f"Function {func.__name__} performance", extra={
                        'function': func.__name__,
                        'duration_ms': duration_ms
                    })

                return result

            except Exception as e:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                logger = get_logger(func.__module__)
                logger.error(f"Error in {func.__name__} after {duration_ms:.2f}ms: {e}", extra={
                    'function': func.__name__,
                    'duration_ms': duration_ms,
                    'error': str(e)
                })
                raise

        return wrapper
    return decorator


class ContextLogger:
    """Context-aware logger that adds contextual information."""

    def __init__(self, name: str, context: Optional[Dict[str, Any]] = None):
        """Initialize context logger."""
        self.logger = get_logger(name)
        self.context = context or {}

    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        extra = {**self.context, **kwargs.get('extra', {})}
        kwargs['extra'] = extra
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message with context."""
        extra = {**self.context, **kwargs.get('extra', {})}
        kwargs['extra'] = extra
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        extra = {**self.context, **kwargs.get('extra', {})}
        kwargs['extra'] = extra
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message with context."""
        extra = {**self.context, **kwargs.get('extra', {})}
        kwargs['extra'] = extra
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        extra = {**self.context, **kwargs.get('extra', {})}
        kwargs['extra'] = extra
        self.logger.critical(message, **kwargs)

    def add_context(self, **kwargs):
        """Add context information."""
        self.context.update(kwargs)

    def remove_context(self, *keys):
        """Remove context information."""
        for key in keys:
            self.context.pop(key, None)

    def clear_context(self):
        """Clear all context information."""
        self.context.clear()