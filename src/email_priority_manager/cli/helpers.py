"""
CLI Helper Functions

This module provides various helper functions for CLI operations including
output formatting, data processing, and common utilities.
"""

import os
import sys
import json
import csv
from typing import Any, Dict, List, Optional, Union, Callable
from pathlib import Path
from datetime import datetime, timezone
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich import box

from .utils.colors import Colors
from .utils.logging import get_logger
from .base import create_table, display_table


logger = get_logger(__name__)
console = Console()


class OutputFormatter:
    """Handles output formatting for different formats."""

    @staticmethod
    def format_as_table(data: List[Dict[str, Any]], columns: List[str], title: str = "") -> Table:
        """Format data as a table."""
        table = create_table(title=title, columns=columns)

        for row in data:
            table_row = []
            for col in columns:
                value = row.get(col, "")
                if isinstance(value, (list, dict)):
                    value = json.dumps(value, indent=2)
                elif isinstance(value, datetime):
                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                elif value is None:
                    value = "N/A"
                table_row.append(str(value))
            table.add_row(*table_row)

        return table

    @staticmethod
    def format_as_json(data: Any, indent: int = 2) -> str:
        """Format data as JSON."""
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, '__dict__'):
                return obj.__dict__
            return str(obj)

        return json.dumps(data, indent=indent, default=json_serializer, ensure_ascii=False)

    @staticmethod
    def format_as_csv(data: List[Dict[str, Any]], columns: List[str]) -> str:
        """Format data as CSV."""
        output = []
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)
        return "\n".join(output)

    @staticmethod
    def format_as_markdown(data: List[Dict[str, Any]], columns: List[str], title: str = "") -> str:
        """Format data as Markdown table."""
        if title:
            output = [f"# {title}\n"]
        else:
            output = []

        # Header
        output.append("| " + " | ".join(columns) + " |")
        output.append("| " + " | ".join(["---" for _ in columns]) + " |")

        # Data rows
        for row in data:
            row_data = []
            for col in columns:
                value = row.get(col, "")
                if isinstance(value, (list, dict)):
                    value = json.dumps(value)
                elif isinstance(value, datetime):
                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                elif value is None:
                    value = "N/A"
                row_data.append(str(value).replace("|", "\\|"))
            output.append("| " + " | ".join(row_data) + " |")

        return "\n".join(output)


class DataProcessor:
    """Common data processing utilities."""

    @staticmethod
    def filter_data(data: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter data based on provided filters."""
        filtered_data = []

        for item in data:
            match = True
            for key, value in filters.items():
                if key not in item:
                    match = False
                    break

                item_value = item[key]

                # Handle different filter types
                if isinstance(value, str):
                    if value.lower() not in str(item_value).lower():
                        match = False
                        break
                elif isinstance(value, (int, float)):
                    if item_value != value:
                        match = False
                        break
                elif isinstance(value, list):
                    if item_value not in value:
                        match = False
                        break
                elif callable(value):
                    if not value(item_value):
                        match = False
                        break

            if match:
                filtered_data.append(item)

        return filtered_data

    @staticmethod
    def sort_data(data: List[Dict[str, Any]], sort_by: str, reverse: bool = False) -> List[Dict[str, Any]]:
        """Sort data by specified field."""
        def sort_key(item):
            value = item.get(sort_by)
            if value is None:
                return ""
            elif isinstance(value, (int, float)):
                return value
            elif isinstance(value, str):
                return value.lower()
            elif isinstance(value, datetime):
                return value.timestamp()
            else:
                return str(value)

        return sorted(data, key=sort_key, reverse=reverse)

    @staticmethod
    def paginate_data(data: List[Dict[str, Any]], page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Paginate data."""
        total_items = len(data)
        total_pages = (total_items + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        page_data = data[start_idx:end_idx]

        return {
            "data": page_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

    @staticmethod
    def group_data(data: List[Dict[str, Any]], group_by: str) -> Dict[str, List[Dict[str, Any]]]:
        """Group data by specified field."""
        groups = {}

        for item in data:
            key = item.get(group_by, "Unknown")
            if key not in groups:
                groups[key] = []
            groups[key].append(item)

        return groups


class FileHelper:
    """File operation helpers."""

    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Ensure directory exists."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def write_file(file_path: Union[str, Path], content: str, mode: str = "w") -> bool:
        """Write content to file."""
        try:
            file_path = Path(file_path)
            FileHelper.ensure_directory(file_path.parent)

            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)

            logger.info(f"File written successfully: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {str(e)}")
            return False

    @staticmethod
    def read_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
        """Read content from file."""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()

        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {str(e)}")
            return None

    @staticmethod
    def append_file(file_path: Union[str, Path], content: str) -> bool:
        """Append content to file."""
        return FileHelper.write_file(file_path, content, mode="a")

    @staticmethod
    def delete_file(file_path: Union[str, Path]) -> bool:
        """Delete file."""
        try:
            file_path = Path(file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False

    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """Get file size in bytes."""
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return 0

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


class ValidationHelper:
    """Input validation helpers."""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        import re
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return re.match(pattern, url) is not None

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe file operations."""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Remove leading/trailing whitespace and dots
        filename = filename.strip('. ')

        # Limit length
        if len(filename) > 255:
            filename = filename[:255]

        return filename

    @staticmethod
    def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Truncate string to maximum length."""
        if len(text) <= max_length:
            return text

        return text[:max_length - len(suffix)] + suffix


class DateTimeHelper:
    """Date and time utilities."""

    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime object."""
        return dt.strftime(format_str)

    @staticmethod
    def parse_datetime(dt_str: str, format_str: Optional[str] = None) -> Optional[datetime]:
        """Parse datetime string."""
        if format_str:
            try:
                return datetime.strptime(dt_str, format_str)
            except ValueError:
                pass

        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue

        # Try ISO format
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except ValueError:
            pass

        return None

    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp as string."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def get_iso_timestamp() -> str:
        """Get current ISO timestamp."""
        return datetime.now(timezone.utc).isoformat()


class InteractiveHelper:
    """Interactive command helpers."""

    @staticmethod
    def confirm_action(message: str, default: bool = False) -> bool:
        """Ask user for confirmation."""
        from .utils.prompts import confirm_action
        return confirm_action(message, default=default)

    @staticmethod
    def select_option(message: str, options: List[str], default: Optional[int] = None) -> int:
        """Let user select from options."""
        console.print(f"{Colors.BLUE}{message}{Colors.RESET}")
        console.print()

        for i, option in enumerate(options, 1):
            if default == i:
                console.print(f"{Colors.GREEN} {i}. {option} (default){Colors.RESET}")
            else:
                console.print(f" {i}. {option}")

        console.print()

        while True:
            try:
                choice = input(f"Select option (1-{len(options)})")
                if not choice and default is not None:
                    return default

                choice = int(choice)
                if 1 <= choice <= len(options):
                    return choice
                else:
                    console.print(f"{Colors.RED}Please enter a number between 1 and {len(options)}{Colors.RESET}")
            except ValueError:
                console.print(f"{Colors.RED}Please enter a valid number{Colors.RESET}")

    @staticmethod
    def prompt_input(message: str, default: Optional[str] = None, required: bool = False) -> str:
        """Prompt user for input."""
        if default:
            prompt = f"{message} [{default}]: "
        else:
            prompt = f"{message}: "

        while True:
            value = input(prompt).strip()

            if not value:
                if default is not None:
                    return default
                elif required:
                    console.print(f"{Colors.RED}This field is required{Colors.RESET}")
                    continue
                else:
                    return ""

            return value


def create_output_handler(format_type: str = "table") -> Callable:
    """Create output handler based on format type."""
    formatters = {
        "table": OutputFormatter.format_as_table,
        "json": OutputFormatter.format_as_json,
        "csv": OutputFormatter.format_as_csv,
        "markdown": OutputFormatter.format_as_markdown
    }

    if format_type not in formatters:
        raise ValueError(f"Unsupported format type: {format_type}")

    return formatters[format_type]


def display_data(data: List[Dict[str, Any]], columns: List[str], format_type: str = "table", title: str = ""):
    """Display data in specified format."""
    formatter = create_output_handler(format_type)

    if format_type == "table":
        table = formatter(data, columns, title)
        display_table(table, title)
    else:
        output = formatter(data, columns, title)
        console.print(output)


def create_tree(data: Dict[str, Any], title: str = "") -> Tree:
    """Create a tree visualization from nested data."""
    tree = Tree(title if title else "Data Structure")

    def add_items(node, items):
        if isinstance(items, dict):
            for key, value in items.items():
                if isinstance(value, (dict, list)):
                    child = node.add(f"{key}:")
                    add_items(child, value)
                else:
                    node.add(f"{key}: {value}")
        elif isinstance(items, list):
            for i, item in enumerate(items):
                if isinstance(item, (dict, list)):
                    child = node.add(f"[{i}]:")
                    add_items(child, item)
                else:
                    node.add(f"[{i}]: {item}")

    add_items(tree, data)
    return tree


def create_summary_stats(data: List[Dict[str, Any]], numeric_fields: List[str]) -> Dict[str, Any]:
    """Create summary statistics for numeric fields."""
    stats = {"total_count": len(data)}

    for field in numeric_fields:
        values = [item.get(field) for item in data if isinstance(item.get(field), (int, float))]
        if values:
            stats[field] = {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "count": len(values)
            }

    return stats


def display_summary_stats(stats: Dict[str, Any], title: str = "Summary Statistics"):
    """Display summary statistics."""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Total Count", str(stats.get("total_count", 0)))

    for field, field_stats in stats.items():
        if field != "total_count":
            table.add_row(f"{field} Count", str(field_stats.get("count", 0)))
            table.add_row(f"{field} Min", str(field_stats.get("min", "N/A")))
            table.add_row(f"{field} Max", str(field_stats.get("max", "N/A")))
            table.add_row(f"{field} Average", f"{field_stats.get('avg', 0):.2f}")

    display_table(table)