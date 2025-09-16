"""
Tests for CLI base functionality.
"""

import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner

from email_priority_manager.cli.base import (
    CLIError, ValidationError, CommandContext, BaseCommand,
    validate_email_ids, validate_date_format, validate_file_path,
    create_table, format_success_message, format_error_message
)


class TestCLIError:
    """Test cases for CLIError class."""

    def test_cli_error_creation(self):
        """Test CLIError creation."""
        error = CLIError("Test error", exit_code=2)
        assert error.message == "Test error"
        assert error.exit_code == 2

    def test_cli_error_defaults(self):
        """Test CLIError default values."""
        error = CLIError("Test error")
        assert error.message == "Test error"
        assert error.exit_code == 1


class TestValidationError:
    """Test cases for ValidationError class."""

    def test_validation_error_creation(self):
        """Test ValidationError creation."""
        error = ValidationError("Validation failed", field="email")
        assert error.message == "Validation failed"
        assert error.field == "email"
        assert error.exit_code == 2

    def test_validation_error_defaults(self):
        """Test ValidationError default values."""
        error = ValidationError("Validation failed")
        assert error.message == "Validation failed"
        assert error.field is None
        assert error.exit_code == 2


class TestCommandContext:
    """Test cases for CommandContext class."""

    def setup_method(self):
        """Set up test environment."""
        self.mock_ctx = Mock()
        self.mock_ctx.obj = {
            'verbose': True,
            'quiet': False,
            'config_file': '/test/config.yaml',
            'log_level': 'DEBUG'
        }
        self.cmd_ctx = CommandContext(self.mock_ctx)

    def test_command_context_initialization(self):
        """Test CommandContext initialization."""
        assert self.cmd_ctx.verbose is True
        assert self.cmd_ctx.quiet is False
        assert self.cmd_ctx.config_file == '/test/config.yaml'
        assert self.cmd_ctx.log_level == 'DEBUG'

    def test_command_context_log_info(self):
        """Test CommandContext info logging."""
        with patch('email_priority_manager.cli.base.console.print') as mock_print:
            self.cmd_ctx.log("Info message")
            mock_print.assert_called_once()
            assert 'Info message' in mock_print.call_args[0][0]

    def test_command_context_log_debug(self):
        """Test CommandContext debug logging."""
        with patch('email_priority_manager.cli.base.console.print') as mock_print:
            self.cmd_ctx.debug("Debug message")
            mock_print.assert_called_once()
            assert 'Debug message' in mock_print.call_args[0][0]

    def test_command_context_log_warning(self):
        """Test CommandContext warning logging."""
        with patch('email_priority_manager.cli.base.console.print') as mock_print:
            self.cmd_ctx.log("Warning message", "WARNING")
            mock_print.assert_called_once()
            assert 'Warning message' in mock_print.call_args[0][0]

    def test_command_context_log_error(self):
        """Test CommandContext error logging."""
        with patch('email_priority_manager.cli.base.console.print') as mock_print:
            self.cmd_ctx.log("Error message", "ERROR")
            mock_print.assert_called_once()
            assert 'Error message' in mock_print.call_args[0][0]

    def test_command_context_success(self):
        """Test CommandContext success message."""
        with patch('email_priority_manager.cli.base.console.print') as mock_print:
            self.cmd_ctx.success("Success message")
            mock_print.assert_called_once()
            assert 'Success message' in mock_print.call_args[0][0]

    def test_command_context_error(self):
        """Test CommandContext error message."""
        with patch('email_priority_manager.cli.base.console.print') as mock_print:
            self.cmd_ctx.error("Error message")
            mock_print.assert_called_once()
            assert 'Error message' in mock_print.call_args[0][0]

    def test_command_context_quiet_mode(self):
        """Test CommandContext quiet mode."""
        quiet_ctx = CommandContext(Mock())
        quiet_ctx.quiet = True

        with patch('email_priority_manager.cli.base.console.print') as mock_print:
            quiet_ctx.log("This should not appear")
            quiet_ctx.success("This should not appear")
            quiet_ctx.error("This should appear")  # Errors always show
            quiet_ctx.debug("This should not appear")

            # Only error should be printed
            assert mock_print.call_count == 1
            assert 'Error message' in mock_print.call_args[0][0]

    def test_command_context_non_verbose_debug(self):
        """Test CommandContext debug logging in non-verbose mode."""
        non_verbose_ctx = CommandContext(Mock())
        non_verbose_ctx.verbose = False
        non_verbose_ctx.quiet = False

        with patch('email_priority_manager.cli.base.console.print') as mock_print:
            non_verbose_ctx.debug("Debug message")
            # Debug should not be printed in non-verbose mode
            mock_print.assert_not_called()


class TestBaseCommand:
    """Test cases for BaseCommand class."""

    def setup_method(self):
        """Set up test environment."""
        self.command = BaseCommand("test", "Test command")

    def test_base_command_initialization(self):
        """Test BaseCommand initialization."""
        assert self.command.name == "test"
        assert self.command.help_text == "Test command"
        assert self.command.validators == []

    def test_base_command_add_validator(self):
        """Test BaseCommand add validator."""
        def dummy_validator():
            pass

        self.command.add_validator(dummy_validator)
        assert len(self.command.validators) == 1
        assert self.command.validators[0] == dummy_validator

    def test_base_command_execute_not_implemented(self):
        """Test BaseCommand execute method raises NotImplementedError."""
        mock_ctx = Mock()
        with pytest.raises(NotImplementedError):
            self.command.execute(mock_ctx)

    def test_base_command_validate_empty_validators(self):
        """Test BaseCommand validate with no validators."""
        mock_ctx = Mock()
        assert self.command.validate(mock_ctx) is True

    def test_base_command_validate_success(self):
        """Test BaseCommand validate with successful validation."""
        def success_validator(ctx, **kwargs):
            return True

        self.command.add_validator(success_validator)
        mock_ctx = Mock()
        assert self.command.validate(mock_ctx) is True

    def test_base_command_validate_failure(self):
        """Test BaseCommand validate with validation failure."""
        def failing_validator(ctx, **kwargs):
            raise ValidationError("Validation failed")

        self.command.add_validator(failing_validator)
        mock_ctx = Mock()
        mock_ctx.error = Mock()

        result = self.command.validate(mock_ctx)
        assert result is False
        mock_ctx.error.assert_called_once_with("Validation failed: Validation failed")

    def test_base_command_handle_cli_error(self):
        """Test BaseCommand handle CLI error."""
        mock_ctx = Mock()
        error = CLIError("Test CLI error")

        self.command.handle_error(error, mock_ctx)
        mock_ctx.error.assert_called_once_with("Test CLI error")

    def test_base_command_handle_general_error(self):
        """Test BaseCommand handle general error."""
        mock_ctx = Mock()
        mock_ctx.verbose = False
        error = Exception("Test general error")

        self.command.handle_error(error, mock_ctx)
        mock_ctx.error.assert_called_once_with("Unexpected error: Test general error")

    def test_base_command_handle_general_error_verbose(self):
        """Test BaseCommand handle general error in verbose mode."""
        mock_ctx = Mock()
        mock_ctx.verbose = True
        error = Exception("Test general error")

        with patch('email_priority_manager.cli.base.traceback') as mock_traceback:
            self.command.handle_error(error, mock_ctx)
            mock_ctx.error.assert_called_once_with("Unexpected error: Test general error")
            mock_traceback.format_exc.assert_called_once()


class TestValidationFunctions:
    """Test cases for validation functions."""

    def test_validate_email_ids_empty(self):
        """Test validate_email_ids with empty list."""
        assert validate_email_ids([]) is True

    def test_validate_email_ids_valid(self):
        """Test validate_email_ids with valid IDs."""
        assert validate_email_ids(['1', '2', '3']) is True

    def test_validate_email_ids_invalid(self):
        """Test validate_email_ids with invalid IDs."""
        with pytest.raises(ValidationError) as exc_info:
            validate_email_ids(['1', 'invalid', '3'])
        assert 'Invalid email ID format: invalid' in str(exc_info.value)
        assert exc_info.value.field == 'email_ids'

    def test_validate_date_format_empty(self):
        """Test validate_date_format with empty string."""
        assert validate_date_format('') is True

    def test_validate_date_format_valid_iso(self):
        """Test validate_date_format with valid ISO format."""
        assert validate_date_format('2024-01-15T10:30:00') is True

    def test_validate_date_format_valid_yyyy_mm_dd(self):
        """Test validate_date_format with valid YYYY-MM-DD format."""
        assert validate_date_format('2024-01-15') is True

    def test_validate_date_format_invalid(self):
        """Test validate_date_format with invalid format."""
        with pytest.raises(ValidationError) as exc_info:
            validate_date_format('invalid-date')
        assert 'Invalid date format: invalid-date' in str(exc_info.value)
        assert exc_info.value.field == 'date'

    def test_validate_file_path_empty(self):
        """Test validate_file_path with empty string."""
        assert validate_file_path('') is True

    @patch('email_priority_manager.cli.base.Path')
    def test_validate_file_path_exists(self, mock_path):
        """Test validate_file_path with existing file."""
        mock_path.return_value.exists.return_value = True

        assert validate_file_path('/test/file.txt', must_exist=True) is True

    @patch('email_priority_manager.cli.base.Path')
    def test_validate_file_path_not_exists(self, mock_path):
        """Test validate_file_path with non-existing file."""
        mock_path.return_value.exists.return_value = False

        with pytest.raises(ValidationError) as exc_info:
            validate_file_path('/test/file.txt', must_exist=True)
        assert 'File does not exist: /test/file.txt' in str(exc_info.value)
        assert exc_info.value.field == 'file_path'

    @patch('email_priority_manager.cli.base.os.access')
    @patch('email_priority_manager.cli.base.Path')
    def test_validate_file_path_writable(self, mock_path, mock_access):
        """Test validate_file_path with writable parent directory."""
        mock_path.return_value.exists.return_value = False
        mock_path.return_value.parent.exists.return_value = True
        mock_access.return_value = True

        assert validate_file_path('/test/new_file.txt', must_writable=True) is True


class TestUtilityFunctions:
    """Test cases for utility functions."""

    def test_create_table(self):
        """Test create_table function."""
        table = create_table("Test Table", ["Col1", "Col2"])
        assert table.title == "Test Table"
        assert len(table.columns) == 2
        assert table.columns[0].header == "Col1"
        assert table.columns[1].header == "Col2"

    def test_create_table_no_title(self):
        """Test create_table function without title."""
        table = create_table(columns=["Col1", "Col2"])
        assert table.title is None
        assert len(table.columns) == 2

    def test_create_table_no_columns(self):
        """Test create_table function without columns."""
        table = create_table("Test Table")
        assert table.title == "Test Table"
        assert len(table.columns) == 0

    def test_format_success_message(self):
        """Test format_success_message function."""
        message = format_success_message("Operation completed")
        assert '✓ Operation completed' in message

    def test_format_error_message(self):
        """Test format_error_message function."""
        message = format_error_message("Operation failed")
        assert '✗ Operation failed' in message

    def test_format_warning_message(self):
        """Test format_warning_message function."""
        message = format_warning_message("Warning message")
        assert '⚠ Warning message' in message

    def test_format_info_message(self):
        """Test format_info_message function."""
        message = format_info_message("Info message")
        assert 'ℹ Info message' in message