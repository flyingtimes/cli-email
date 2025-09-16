"""
Tests for CLI help system.
"""

import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner

from email_priority_manager.cli.commands.help import help_command
from email_priority_manager.cli.framework.help import (
    HelpTopic, CommandHelp, HelpSystem, get_help_system
)


class TestHelpTopic:
    """Test cases for HelpTopic class."""

    def test_help_topic_creation(self):
        """Test HelpTopic creation."""
        topic = HelpTopic(
            title="Test Topic",
            description="Test description",
            examples=["example1", "example2"],
            options=[{"option": "--test", "description": "Test option"}],
            see_also=["related-topic"],
            category="test"
        )

        assert topic.title == "Test Topic"
        assert topic.description == "Test description"
        assert topic.examples == ["example1", "example2"]
        assert topic.options == [{"option": "--test", "description": "Test option"}]
        assert topic.see_also == ["related-topic"]
        assert topic.category == "test"

    def test_help_topic_defaults(self):
        """Test HelpTopic default values."""
        topic = HelpTopic("Test", "Description", [], [], [])

        assert topic.category == "general"


class TestCommandHelp:
    """Test cases for CommandHelp class."""

    def test_command_help_creation(self):
        """Test CommandHelp creation."""
        command = CommandHelp(
            name="test-command",
            description="Test command description",
            usage="test-command [OPTIONS]",
            options=[{"option": "--test", "description": "Test option"}],
            examples=["test-command --test"],
            notes=["Note 1", "Note 2"],
            category="commands"
        )

        assert command.name == "test-command"
        assert command.description == "Test command description"
        assert command.usage == "test-command [OPTIONS]"
        assert command.options == [{"option": "--test", "description": "Test option"}]
        assert command.examples == ["test-command --test"]
        assert command.notes == ["Note 1", "Note 2"]
        assert command.category == "commands"

    def test_command_help_defaults(self):
        """Test CommandHelp default values."""
        command = CommandHelp("test", "desc", "usage", [], [], [])

        assert command.category == "commands"


class TestHelpSystem:
    """Test cases for HelpSystem class."""

    def setup_method(self):
        """Set up test environment."""
        self.help_system = HelpSystem()

    def test_help_system_creation(self):
        """Test HelpSystem creation."""
        assert len(self.help_system.topics) > 0  # Should have default topics
        assert len(self.help_system.categories) > 0
        assert self.help_system.commands == {}

    def test_add_topic(self):
        """Test adding a help topic."""
        topic = HelpTopic("New Topic", "Description", [], [], [], "new-category")

        self.help_system.add_topic("new-topic", topic)

        assert "new-topic" in self.help_system.topics
        assert self.help_system.topics["new-topic"] == topic
        assert "new-category" in self.help_system.categories
        assert "new-topic" in self.help_system.categories["new-category"]

    def test_add_command_help(self):
        """Test adding command help."""
        command = CommandHelp("test-cmd", "Description", "usage", [], [], [])

        self.help_system.add_command_help("test-cmd", command)

        assert "test-cmd" in self.help_system.commands
        assert self.help_system.commands["test-cmd"] == command

    def test_get_help_system_singleton(self):
        """Test get_help_system returns singleton instance."""
        system1 = get_help_system()
        system2 = get_help_system()

        assert system1 is system2

    def test_search_help_found(self):
        """Test search_help with matching results."""
        results = self.help_system.search_help("configuration")

        assert len(results) > 0
        # Should find configuration topic
        assert any("configuration" in result for result in results)

    def test_search_help_not_found(self):
        """Test search_help with no matching results."""
        results = self.help_system.search_help("nonexistent-topic-xyz")

        assert len(results) == 0

    def test_search_help_case_insensitive(self):
        """Test search_help is case insensitive."""
        results_lower = self.help_system.search_help("configuration")
        results_upper = self.help_system.search_help("CONFIGURATION")

        assert len(results_lower) == len(results_upper)

    def test_search_help_partial_match(self):
        """Test search_help with partial matches."""
        results = self.help_system.search_help("config")

        assert len(results) > 0
        # Should find configuration topic
        assert any("configuration" in result for result in results)


class TestHelpCommand:
    """Test cases for help command."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @patch('email_priority_manager.cli.commands.help.get_help_system')
    def test_help_command_no_args(self, mock_get_help_system):
        """Test help command with no arguments."""
        mock_help_system = Mock()
        mock_get_help_system.return_value = mock_help_system

        result = self.runner.invoke(help_command, [])

        assert result.exit_code == 0
        mock_help_system.show_help_overview.assert_called_once()

    @patch('email_priority_manager.cli.commands.help.get_help_system')
    def test_help_command_with_topic(self, mock_get_help_system):
        """Test help command with topic argument."""
        mock_help_system = Mock()
        mock_help_system.topics = {"getting-started": Mock()}
        mock_get_help_system.return_value = mock_help_system

        result = self.runner.invoke(help_command, ['getting-started'])

        assert result.exit_code == 0
        mock_help_system.show_topic_help.assert_called_once_with("getting-started")

    @patch('email_priority_manager.cli.commands.help.get_help_system')
    def test_help_command_with_command(self, mock_get_help_system):
        """Test help command with command argument."""
        mock_help_system = Mock()
        mock_help_system.commands = {"test-cmd": Mock()}
        mock_get_help_system.return_value = mock_help_system

        result = self.runner.invoke(help_command, ['test-cmd'])

        assert result.exit_code == 0
        mock_help_system.show_command_help.assert_called_once_with("test-cmd")

    @patch('email_priority_manager.cli.commands.help.get_help_system')
    def test_help_command_search(self, mock_get_help_system):
        """Test help command with search option."""
        mock_help_system = Mock()
        mock_help_system.search_help.return_value = ["topic:config", "command:cmd"]
        mock_get_help_system.return_value = mock_help_system

        result = self.runner.invoke(help_command, ['--search', 'config'])

        assert result.exit_code == 0
        mock_help_system.search_help.assert_called_once_with("config")

    @patch('email_priority_manager.cli.commands.help.get_help_system')
    def test_help_command_list_topics(self, mock_get_help_system):
        """Test help command with list-topics option."""
        mock_help_system = Mock()
        mock_get_help_system.return_value = mock_help_system

        result = self.runner.invoke(help_command, ['--list-topics'])

        assert result.exit_code == 0
        mock_help_system.show_all_topics.assert_called_once()

    @patch('email_priority_manager.cli.commands.help.get_help_system')
    def test_help_command_list_commands(self, mock_get_help_system):
        """Test help command with list-commands option."""
        mock_help_system = Mock()
        mock_get_help_system.return_value = mock_help_system

        result = self.runner.invoke(help_command, ['--list-commands'])

        assert result.exit_code == 0
        mock_help_system.show_all_commands.assert_called_once()

    @patch('email_priority_manager.cli.commands.help.get_help_system')
    def test_help_command_unknown_topic(self, mock_get_help_system):
        """Test help command with unknown topic."""
        mock_help_system = Mock()
        mock_help_system.topics = {}
        mock_help_system.commands = {}
        mock_get_help_system.return_value = mock_help_system

        result = self.runner.invoke(help_command, ['unknown-topic'])

        assert result.exit_code == 1
        assert "Topic 'unknown-topic' not found" in result.output

    @patch('email_priority_manager.cli.commands.help.get_help_system')
    def test_help_command_topic_suggestions(self, mock_get_help_system):
        """Test help command provides topic suggestions."""
        mock_help_system = Mock()
        mock_help_system.topics = {"getting-started": Mock()}
        mock_help_system.commands = {}
        mock_get_help_system.return_value = mock_help_system

        result = self.runner.invoke(help_command, ['getting'])

        assert result.exit_code == 1
        assert "Topic 'getting' not found" in result.output
        assert "Did you mean:" in result.output

    @patch('email_priority_manager.cli.commands.help.get_help_system')
    def test_help_command_exception_handling(self, mock_get_help_system):
        """Test help command exception handling."""
        mock_help_system = Mock()
        mock_help_system.show_help_overview.side_effect = Exception("Test error")
        mock_get_help_system.return_value = mock_help_system

        result = self.runner.invoke(help_command, [])

        assert result.exit_code == 1
        assert "Error displaying help: Test error" in result.output


class TestCommandHelpSetup:
    """Test cases for command help setup."""

    @patch('email_priority_manager.cli.commands.help.get_help_system')
    def test_setup_command_help(self, mock_get_help_system):
        """Test setup_command_help function."""
        from email_priority_manager.cli.commands.help import setup_command_help

        mock_help_system = Mock()
        mock_get_help_system.return_value = mock_help_system

        setup_command_help()

        # Should add help for main and help commands
        assert mock_help_system.add_command_help.call_count >= 2

    @patch('email_priority_manager.cli.commands.help.get_help_system')
    def test_register_help_command(self, mock_get_help_system):
        """Test register_help_command function."""
        from email_priority_manager.cli.commands.help import register_help_command
        import click

        mock_help_system = Mock()
        mock_get_help_system.return_value = mock_help_system

        # Create a mock CLI group
        @click.group()
        def cli():
            pass

        register_help_command(cli)

        # Help command should be added to the CLI group
        assert 'help' in cli.commands
        assert isinstance(cli.commands['help'], click.Command)