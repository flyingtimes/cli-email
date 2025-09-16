"""
Tests for CLI main functionality.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from email_priority_manager.cli.main import cli


class TestCLIMain:
    """Test cases for CLI main functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @patch('email_priority_manager.cli.main.setup_cli_framework')
    @patch('email_priority_manager.cli.main.setup_cli_logging')
    def test_cli_help(self, mock_logging, mock_framework):
        """Test CLI help command."""
        result = self.runner.invoke(cli, ['--help'])

        assert result.exit_code == 0
        assert 'Email Priority Manager' in result.output
        assert 'Intelligent email classification' in result.output
        assert '--verbose' in result.output
        assert '--config-file' in result.output
        assert '--help' in result.output

    @patch('email_priority_manager.cli.main.setup_cli_framework')
    @patch('email_priority_manager.cli.main.setup_cli_logging')
    def test_cli_version(self, mock_logging, mock_framework):
        """Test CLI version command."""
        result = self.runner.invoke(cli, ['--version'])

        assert result.exit_code == 0
        assert 'Email Priority Manager version 0.1.0' in result.output

    @patch('email_priority_manager.cli.main.setup_cli_framework')
    @patch('email_priority_manager.cli.main.setup_cli_logging')
    @patch('email_priority_manager.cli.main.display_welcome_message')
    def test_cli_no_command_shows_welcome(self, mock_welcome, mock_logging, mock_framework):
        """Test CLI shows welcome message when no command provided."""
        result = self.runner.invoke(cli, [])

        assert result.exit_code == 0
        mock_welcome.assert_called_once()

    @patch('email_priority_manager.cli.main.setup_cli_framework')
    @patch('email_priority_manager.cli.main.setup_cli_logging')
    def test_cli_verbose_option(self, mock_logging, mock_framework):
        """Test CLI verbose option."""
        result = self.runner.invoke(cli, ['--verbose', '--help'])

        assert result.exit_code == 0
        # Verify that verbose flag is processed (framework should be called with verbose=True)
        mock_framework.assert_called_once()
        call_args = mock_framework.call_args[0][0]
        assert call_args.get('verbose') is True

    @patch('email_priority_manager.cli.main.setup_cli_framework')
    @patch('email_priority_manager.cli.main.setup_cli_logging')
    def test_cli_quiet_option(self, mock_logging, mock_framework):
        """Test CLI quiet option."""
        result = self.runner.invoke(cli, ['--quiet', '--help'])

        assert result.exit_code == 0
        # Verify that quiet flag is processed (framework should be called with quiet=True)
        mock_framework.assert_called_once()
        call_args = mock_framework.call_args[0][0]
        assert call_args.get('quiet') is True

    @patch('email_priority_manager.cli.main.setup_cli_framework')
    @patch('email_priority_manager.cli.main.setup_cli_logging')
    def test_cli_log_level_option(self, mock_logging, mock_framework):
        """Test CLI log level option."""
        result = self.runner.invoke(cli, ['--log-level', 'DEBUG', '--help'])

        assert result.exit_code == 0
        # Verify that log level is processed
        mock_framework.assert_called_once()
        call_args = mock_framework.call_args[0][0]
        assert call_args.get('log_level') == 'DEBUG'

    @patch('email_priority_manager.cli.main.setup_cli_framework')
    @patch('email_priority_manager.cli.main.setup_cli_logging')
    def test_cli_invalid_log_level(self, mock_logging, mock_framework):
        """Test CLI invalid log level option."""
        result = self.runner.invoke(cli, ['--log-level', 'INVALID', '--help'])

        assert result.exit_code != 0
        assert 'Invalid value for' in result.output

    @patch('email_priority_manager.cli.main.setup_cli_framework')
    @patch('email_priority_manager.cli.main.setup_cli_logging')
    def test_cli_keyboard_interrupt_handling(self, mock_logging, mock_framework):
        """Test CLI keyboard interrupt handling."""
        with patch('email_priority_manager.cli.main.cli') as mock_cli:
            mock_cli.side_effect = KeyboardInterrupt()

            with patch('email_priority_manager.cli.main.console.print') as mock_print:
                result = self.runner.invoke(cli, [])

                # The result will be 130 (keyboard interrupt exit code)
                assert mock_print.called
                # Check that the keyboard interrupt message was printed
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                assert any('Operation cancelled by user' in str(call) for call in print_calls)

    @patch('email_priority_manager.cli.main.setup_cli_framework')
    @patch('email_priority_manager.cli.main.setup_cli_logging')
    def test_cli_general_exception_handling(self, mock_logging, mock_framework):
        """Test CLI general exception handling."""
        with patch('email_priority_manager.cli.main.cli') as mock_cli:
            mock_cli.side_effect = Exception("Test exception")

            with patch('email_priority_manager.cli.main.console.print') as mock_print:
                result = self.runner.invoke(cli, [])

                # The result will be 1 (general error exit code)
                assert mock_print.called
                # Check that the error message was printed
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                assert any('Error: Test exception' in str(call) for call in print_calls)

    @patch('email_priority_manager.cli.main.setup_cli_framework')
    @patch('email_priority_manager.cli.main.setup_cli_logging')
    def test_cli_config_file_option(self, mock_logging, mock_framework):
        """Test CLI config file option."""
        test_config = '/path/to/config.yaml'
        result = self.runner.invoke(cli, ['--config-file', test_config, '--help'])

        assert result.exit_code == 0
        # Verify that config file is processed
        mock_framework.assert_called_once()
        call_args = mock_framework.call_args[0][0]
        assert call_args.get('config_file') == test_config

    @patch('email_priority_manager.cli.main.setup_cli_framework')
    @patch('email_priority_manager.cli.main.setup_cli_logging')
    def test_cli_groups_exist(self, mock_logging, mock_framework):
        """Test that CLI command groups exist."""
        # Test setup group
        result = self.runner.invoke(cli, ['setup', '--help'])
        assert result.exit_code == 0
        assert 'Setup and configuration commands' in result.output

        # Test email group
        result = self.runner.invoke(cli, ['email', '--help'])
        assert result.exit_code == 0
        assert 'Email processing and management commands' in result.output

        # Test query group
        result = self.runner.invoke(cli, ['query', '--help'])
        assert result.exit_code == 0
        assert 'Query and display commands' in result.output

        # Test data group
        result = self.runner.invoke(cli, ['data', '--help'])
        assert result.exit_code == 0
        assert 'Data management and export commands' in result.output