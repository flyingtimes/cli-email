"""
Progress Indicators

This module provides progress indicators and spinners for long-running CLI operations.
"""

import time
from typing import Optional, List, Any, Callable
from dataclasses import dataclass
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
    MofNCompleteColumn,
    DownloadColumn,
    TransferSpeedColumn
)
from rich.console import Console
from rich.text import Text
from rich.panel import Panel

from .utils.colors import Colors


@dataclass
class ProgressTask:
    """Represents a progress tracking task."""
    task_id: str
    description: str
    total: Optional[float] = None
    completed: float = 0
    unit: str = "items"
    show_progress: bool = True
    show_stats: bool = True


class ProgressManager:
    """Manages progress indicators for CLI operations."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.progress: Optional[Progress] = None
        self.tasks: dict[str, ProgressTask] = {}
        self.active_task_ids: List[str] = []

    def create_progress(
        self,
        description: str = "Processing...",
        total: Optional[float] = None,
        unit: str = "items",
        show_progress: bool = True,
        show_stats: bool = True,
        show_speed: bool = False,
        show_time: bool = True
    ) -> Progress:
        """Create a progress indicator with specified options."""
        columns = []

        # Always show spinner and description
        columns.append(SpinnerColumn())
        columns.append(TextColumn("[progress.description]{task.description}"))

        # Show progress bar if requested
        if show_progress and total is not None:
            columns.append(BarColumn())
            columns.append(TaskProgressColumn())

        # Show completion count if total is known
        if show_stats and total is not None:
            columns.append(MofNCompleteColumn())

        # Show speed if requested
        if show_speed:
            columns.append(TransferSpeedColumn())

        # Show time if requested
        if show_time:
            columns.append(TimeElapsedColumn())
            if total is not None:
                columns.append(TimeRemainingColumn())

        self.progress = Progress(*columns, console=self.console)
        return self.progress

    def add_task(
        self,
        task_id: str,
        description: str,
        total: Optional[float] = None,
        unit: str = "items",
        show_progress: bool = True,
        show_stats: bool = True
    ) -> ProgressTask:
        """Add a new task to track progress."""
        if task_id in self.tasks:
            raise ValueError(f"Task ID '{task_id}' already exists")

        task = ProgressTask(
            task_id=task_id,
            description=description,
            total=total,
            unit=unit,
            show_progress=show_progress,
            show_stats=show_stats
        )

        self.tasks[task_id] = task
        return task

    def update_task(self, task_id: str, advance: float = 1, description: Optional[str] = None):
        """Update task progress."""
        if task_id not in self.tasks:
            raise ValueError(f"Task ID '{task_id}' not found")

        task = self.tasks[task_id]
        task.completed += advance

        if description:
            task.description = description

        # Update rich progress if available
        if self.progress and hasattr(self.progress, 'update'):
            # Find the rich task ID
            rich_task_id = None
            for i, t in enumerate(self.progress.tasks):
                if t.description.startswith(task.description.split(' (')[0]):
                    rich_task_id = i
                    break

            if rich_task_id is not None:
                self.progress.update(rich_task_id, advance=advance, description=task.description)

    def complete_task(self, task_id: str):
        """Mark a task as completed."""
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        if task.total:
            task.completed = task.total

        # Update rich progress if available
        if self.progress and hasattr(self.progress, 'update'):
            rich_task_id = None
            for i, t in enumerate(self.progress.tasks):
                if t.description.startswith(task.description.split(' (')[0]):
                    rich_task_id = i
                    break

            if rich_task_id is not None:
                self.progress.update(rich_task_id, completed=task.total)

    def get_task_progress(self, task_id: str) -> float:
        """Get progress percentage for a task."""
        if task_id not in self.tasks:
            return 0.0

        task = self.tasks[task_id]
        if task.total is None or task.total == 0:
            return 0.0

        return min(100.0, (task.completed / task.total) * 100)

    def is_task_complete(self, task_id: str) -> bool:
        """Check if a task is complete."""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        if task.total is None:
            return False

        return task.completed >= task.total

    def remove_task(self, task_id: str):
        """Remove a task from tracking."""
        if task_id in self.tasks:
            del self.tasks[task_id]

    def clear_all_tasks(self):
        """Clear all tracked tasks."""
        self.tasks.clear()
        self.active_task_ids.clear()

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all tracked tasks."""
        summary = {
            "total_tasks": len(self.tasks),
            "completed_tasks": sum(1 for task in self.tasks.values() if self.is_task_complete(task.task_id)),
            "active_tasks": len(self.active_task_ids),
            "tasks": {}
        }

        for task_id, task in self.tasks.items():
            summary["tasks"][task_id] = {
                "description": task.description,
                "total": task.total,
                "completed": task.completed,
                "progress": self.get_task_progress(task_id),
                "is_complete": self.is_task_complete(task_id)
            }

        return summary


def create_progress_indicator(
    description: str = "Processing...",
    total: Optional[float] = None,
    unit: str = "items",
    show_progress: bool = True,
    show_stats: bool = True,
    show_speed: bool = False,
    show_time: bool = True
) -> Progress:
    """Create a progress indicator with sensible defaults."""
    console = Console()
    progress_manager = ProgressManager(console)

    return progress_manager.create_progress(
        description=description,
        total=total,
        unit=unit,
        show_progress=show_progress,
        show_stats=show_stats,
        show_speed=show_speed,
        show_time=show_time
    )


def create_spinner(description: str = "Working...") -> Progress:
    """Create a simple spinner for indeterminate operations."""
    return create_progress_indicator(
        description=description,
        total=None,
        show_progress=False,
        show_stats=False,
        show_speed=False,
        show_time=False
    )


def create_progress_bar(
    description: str = "Processing...",
    total: float = 100,
    unit: str = "items"
) -> Progress:
    """Create a progress bar for determinate operations."""
    return create_progress_indicator(
        description=description,
        total=total,
        unit=unit,
        show_progress=True,
        show_stats=True,
        show_speed=True,
        show_time=True
    )


class SimpleProgress:
    """Simple progress indicator for basic operations."""

    def __init__(self, description: str = "Processing...", total: int = 100):
        self.description = description
        self.total = total
        self.current = 0
        self.start_time = time.time()

    def update(self, advance: int = 1):
        """Update progress."""
        self.current += advance
        self._display()

    def set_description(self, description: str):
        """Update the description."""
        self.description = description
        self._display()

    def _display(self):
        """Display current progress."""
        if self.total > 0:
            percentage = (self.current / self.total) * 100
            bar_length = 20
            filled_length = int(bar_length * self.current // self.total)
            bar = "█" * filled_length + "-" * (bar_length - filled_length)

            elapsed = time.time() - self.start_time
            if self.current > 0:
                eta = (elapsed / self.current) * (self.total - self.current)
                eta_str = f"ETA: {eta:.1f}s"
            else:
                eta_str = "ETA: --"

            print(f"\r{self.description}: |{bar}| {percentage:.1f}% ({self.current}/{self.total}) [{eta_str}]", end="", flush=True)
        else:
            elapsed = time.time() - self.start_time
            print(f"\r{self.description}: {self.current} items ({elapsed:.1f}s)", end="", flush=True)

    def finish(self):
        """Mark progress as finished."""
        self.current = self.total
        self._display()
        print()  # New line after progress completes


def create_simple_progress(description: str = "Processing...", total: int = 100) -> SimpleProgress:
    """Create a simple progress indicator."""
    return SimpleProgress(description, total)