"""
Tests for CLI progress indicators.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from rich.progress import Progress

from email_priority_manager.cli.progress import (
    ProgressTask, ProgressManager, create_progress_indicator,
    create_spinner, create_progress_bar, SimpleProgress,
    create_simple_progress
)


class TestProgressTask:
    """Test cases for ProgressTask class."""

    def test_progress_task_creation(self):
        """Test ProgressTask creation."""
        task = ProgressTask(
            task_id="test_task",
            description="Test task",
            total=100,
            unit="items"
        )

        assert task.task_id == "test_task"
        assert task.description == "Test task"
        assert task.total == 100
        assert task.completed == 0
        assert task.unit == "items"
        assert task.show_progress is True
        assert task.show_stats is True

    def test_progress_task_defaults(self):
        """Test ProgressTask default values."""
        task = ProgressTask("test", "Test")

        assert task.total is None
        assert task.completed == 0
        assert task.unit == "items"
        assert task.show_progress is True
        assert task.show_stats is True


class TestProgressManager:
    """Test cases for ProgressManager class."""

    def setup_method(self):
        """Set up test environment."""
        self.manager = ProgressManager()

    def test_progress_manager_creation(self):
        """Test ProgressManager creation."""
        assert self.manager.progress is None
        assert self.manager.tasks == {}
        assert self.manager.active_task_ids == []

    def test_add_task(self):
        """Test adding a task."""
        task = self.manager.add_task(
            task_id="test_task",
            description="Test task",
            total=100
        )

        assert isinstance(task, ProgressTask)
        assert "test_task" in self.manager.tasks
        assert self.manager.tasks["test_task"] == task

    def test_add_task_duplicate_id(self):
        """Test adding task with duplicate ID."""
        self.manager.add_task("test", "Test task")

        with pytest.raises(ValueError) as exc_info:
            self.manager.add_task("test", "Another task")
        assert "Task ID 'test' already exists" in str(exc_info.value)

    def test_update_task(self):
        """Test updating task progress."""
        task = self.manager.add_task("test", "Test", total=100)
        self.manager.update_task("test", advance=10)

        assert task.completed == 10

    def test_update_task_nonexistent(self):
        """Test updating non-existent task."""
        with pytest.raises(ValueError) as exc_info:
            self.manager.update_task("nonexistent", advance=10)
        assert "Task ID 'nonexistent' not found" in str(exc_info.value)

    def test_update_task_with_description(self):
        """Test updating task with new description."""
        task = self.manager.add_task("test", "Original description")
        self.manager.update_task("test", advance=5, description="New description")

        assert task.completed == 5
        assert task.description == "New description"

    def test_complete_task(self):
        """Test completing a task."""
        task = self.manager.add_task("test", "Test", total=100)
        task.completed = 50
        self.manager.complete_task("test")

        assert task.completed == 100

    def test_complete_task_no_total(self):
        """Test completing a task without total."""
        task = self.manager.add_task("test", "Test", total=None)
        task.completed = 50
        self.manager.complete_task("test")

        assert task.completed == 50  # Should not change when total is None

    def test_complete_task_nonexistent(self):
        """Test completing non-existent task should not raise error."""
        # This should not raise an error
        self.manager.complete_task("nonexistent")

    def test_get_task_progress(self):
        """Test getting task progress."""
        task = self.manager.add_task("test", "Test", total=100)
        task.completed = 30

        progress = self.manager.get_task_progress("test")
        assert progress == 30.0

    def test_get_task_progress_no_total(self):
        """Test getting task progress when total is None."""
        task = self.manager.add_task("test", "Test", total=None)
        task.completed = 30

        progress = self.manager.get_task_progress("test")
        assert progress == 0.0

    def test_get_task_progress_zero_total(self):
        """Test getting task progress when total is zero."""
        task = self.manager.add_task("test", "Test", total=0)
        task.completed = 30

        progress = self.manager.get_task_progress("test")
        assert progress == 0.0

    def test_get_task_progress_over_100(self):
        """Test getting task progress when completed exceeds total."""
        task = self.manager.add_task("test", "Test", total=100)
        task.completed = 150

        progress = self.manager.get_task_progress("test")
        assert progress == 100.0  # Should be capped at 100%

    def test_is_task_complete(self):
        """Test checking if task is complete."""
        task = self.manager.add_task("test", "Test", total=100)
        task.completed = 100

        assert self.manager.is_task_complete("test") is True

    def test_is_task_complete_incomplete(self):
        """Test checking if task is incomplete."""
        task = self.manager.add_task("test", "Test", total=100)
        task.completed = 50

        assert self.manager.is_task_complete("test") is False

    def test_is_task_complete_no_total(self):
        """Test checking if task is complete when total is None."""
        task = self.manager.add_task("test", "Test", total=None)
        task.completed = 50

        assert self.manager.is_task_complete("test") is False

    def test_remove_task(self):
        """Test removing a task."""
        self.manager.add_task("test", "Test")
        self.manager.remove_task("test")

        assert "test" not in self.manager.tasks

    def test_remove_task_nonexistent(self):
        """Test removing non-existent task should not raise error."""
        # This should not raise an error
        self.manager.remove_task("nonexistent")

    def test_clear_all_tasks(self):
        """Test clearing all tasks."""
        self.manager.add_task("test1", "Test 1")
        self.manager.add_task("test2", "Test 2")
        self.manager.active_task_ids = ["test1", "test2"]

        self.manager.clear_all_tasks()

        assert self.manager.tasks == {}
        assert self.manager.active_task_ids == []

    def test_get_summary(self):
        """Test getting progress summary."""
        task1 = self.manager.add_task("task1", "Task 1", total=100)
        task1.completed = 50

        task2 = self.manager.add_task("task2", "Task 2", total=50)
        task2.completed = 50

        summary = self.manager.get_summary()

        assert summary["total_tasks"] == 2
        assert summary["completed_tasks"] == 1
        assert summary["active_tasks"] == 0
        assert "tasks" in summary
        assert "task1" in summary["tasks"]
        assert "task2" in summary["tasks"]

        task1_summary = summary["tasks"]["task1"]
        assert task1_summary["progress"] == 50.0
        assert task1_summary["is_complete"] is False

        task2_summary = summary["tasks"]["task2"]
        assert task2_summary["progress"] == 100.0
        assert task2_summary["is_complete"] is True


class TestProgressIndicatorCreation:
    """Test cases for progress indicator creation functions."""

    def test_create_progress_indicator(self):
        """Test create_progress_indicator function."""
        progress = create_progress_indicator("Processing", total=100)

        assert isinstance(progress, Progress)

    def test_create_spinner(self):
        """Test create_spinner function."""
        spinner = create_spinner("Working...")

        assert isinstance(spinner, Progress)

    def test_create_progress_bar(self):
        """Test create_progress_bar function."""
        progress_bar = create_progress_bar("Processing", total=100)

        assert isinstance(progress_bar, Progress)


class TestSimpleProgress:
    """Test cases for SimpleProgress class."""

    def setup_method(self):
        """Set up test environment."""
        with patch('builtins.print') as mock_print:
            self.progress = SimpleProgress("Test Progress", 100)

    def test_simple_progress_creation(self):
        """Test SimpleProgress creation."""
        assert self.progress.description == "Test Progress"
        assert self.progress.total == 100
        assert self.progress.current == 0
        assert self.progress.start_time is not None

    def test_simple_progress_update(self):
        """Test SimpleProgress update."""
        with patch('builtins.print') as mock_print:
            self.progress.update(10)

        assert self.progress.current == 10
        # Print should be called with progress bar
        mock_print.assert_called_once()

    def test_simple_progress_set_description(self):
        """Test SimpleProgress set description."""
        with patch('builtins.print') as mock_print:
            self.progress.set_description("New Description")

        assert self.progress.description == "New Description"
        # Print should be called
        mock_print.assert_called_once()

    def test_simple_progress_finish(self):
        """Test SimpleProgress finish."""
        with patch('builtins.print') as mock_print:
            self.progress.finish()

        assert self.progress.current == 100
        # Print should be called twice (update and final newline)
        assert mock_print.call_count == 2

    def test_simple_progress_display_complete(self):
        """Test SimpleProgress display when complete."""
        self.progress.current = 100
        self.progress.total = 100

        with patch('builtins.print') as mock_print:
            self.progress._display()

        # Should show 100% complete
        call_args = mock_print.call_args[0][0]
        assert "100%" in call_args

    def test_simple_progress_display_partial(self):
        """Test SimpleProgress display when partially complete."""
        self.progress.current = 30
        self.progress.total = 100

        with patch('builtins.print') as mock_print:
            self.progress._display()

        # Should show 30% complete
        call_args = mock_print.call_args[0][0]
        assert "30%" in call_args

    def test_simple_progress_display_no_total(self):
        """Test SimpleProgress display when total is unknown."""
        self.progress.total = 0
        self.progress.current = 30

        with patch('builtins.print') as mock_print:
            self.progress._display()

        # Should show item count without percentage
        call_args = mock_print.call_args[0][0]
        assert "30 items" in call_args

    @patch('time.time')
    def test_simple_progress_eta_calculation(self, mock_time):
        """Test SimpleProgress ETA calculation."""
        # Mock time progression
        mock_time.side_effect = [0, 10]  # Start time, then 10 seconds later

        progress = SimpleProgress("Test", 100)
        progress.current = 20

        with patch('builtins.print') as mock_print:
            progress._display()

        # Should calculate ETA based on current progress
        call_args = mock_print.call_args[0][0]
        assert "ETA:" in call_args


class TestCreateSimpleProgress:
    """Test cases for create_simple_progress function."""

    def test_create_simple_progress(self):
        """Test create_simple_progress function."""
        with patch('builtins.print'):
            progress = create_simple_progress("Test", 50)

        assert isinstance(progress, SimpleProgress)
        assert progress.description == "Test"
        assert progress.total == 50

    def test_create_simple_progress_defaults(self):
        """Test create_simple_progress with defaults."""
        with patch('builtins.print'):
            progress = create_simple_progress("Test")

        assert progress.description == "Test"
        assert progress.total == 100


class TestProgressDecorators:
    """Test cases for progress decorator functions."""

    def test_with_progress_tracking_decorator(self):
        """Test with_progress_tracking decorator."""
        from email_priority_manager.cli.progress import with_progress_tracking

        @with_progress_tracking("Processing", total=100)
        def test_function(progress_manager, *args, **kwargs):
            progress_manager.update_task("test_function", advance=50)
            return "success"

        result = test_function()
        assert result == "success"

    def test_create_multi_stage_progress(self):
        """Test create_multi_stage_progress function."""
        from email_priority_manager.cli.progress import create_multi_stage_progress

        stages = ["Stage 1", "Stage 2", "Stage 3"]
        manager = create_multi_stage_progress(stages)

        assert len(manager.tasks) == 3
        assert "stage_0" in manager.tasks
        assert "stage_1" in manager.tasks
        assert "stage_2" in manager.tasks

    def test_advance_stage(self):
        """Test advance_stage function."""
        from email_priority_manager.cli.progress import create_multi_stage_progress, advance_stage

        stages = ["Stage 1", "Stage 2"]
        manager = create_multi_stage_progress(stages)

        advance_stage(manager, 0)

        # Stage 0 should be complete
        assert manager.is_task_complete("stage_0") is True

        # Stage 1 should have updated description
        stage_1 = manager.tasks["stage_1"]
        assert "→ Stage" in stage_1.description