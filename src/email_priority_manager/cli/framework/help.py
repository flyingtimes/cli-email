"""
Help System for CLI

This module provides comprehensive help generation and documentation utilities.
"""

import textwrap
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.tree import Tree
from rich import box

from ..utils.colors import Colors, ColorScheme, StyledOutput
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class HelpTopic:
    """Represents a help topic."""
    title: str
    description: str
    examples: List[str]
    options: List[Dict[str, Any]]
    see_also: List[str]
    category: str = "general"


@dataclass
class CommandHelp:
    """Help information for a command."""
    name: str
    description: str
    usage: str
    options: List[Dict[str, Any]]
    examples: List[str]
    notes: List[str]
    category: str = "commands"


class HelpSystem:
    """Comprehensive help system for CLI."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.topics: Dict[str, HelpTopic] = {}
        self.commands: Dict[str, CommandHelp] = {}
        self.categories: Dict[str, List[str]] = {}
        self._setup_default_topics()

    def _setup_default_topics(self):
        """Set up default help topics."""
        self.topics = {
            "getting-started": HelpTopic(
                title="Getting Started",
                description="""
Welcome to Email Priority Manager! This guide will help you get started with
managing your emails using AI-powered classification and organization.

Quick Start:
1. Initialize the system: email-priority-manager init
2. Configure your email: email-priority-manager config set email.provider your_provider
3. Scan your mailbox: email-priority-manager scan
4. Classify emails: email-priority-manager classify
5. View results: email-priority-manager list
                """,
                examples=[
                    "email-priority-manager init",
                    "email-priority-manager scan --limit 50",
                    "email-priority-manager classify --model bigmodel"
                ],
                options=[],
                see_also=["configuration", "commands"],
                category="basics"
            ),
            "configuration": HelpTopic(
                title="Configuration",
                description="""
The Email Priority Manager uses a configuration file to store settings for
email providers, AI models, and other preferences.

Configuration is stored in ~/.email-priority-manager/config.yaml by default.
You can specify a different configuration file using the --config-file option.

Key configuration sections:
- email: Email provider settings (IMAP, SMTP)
- ai: AI model configuration
- database: Database connection settings
- cli: CLI behavior settings
                """,
                examples=[
                    "email-priority-manager config show",
                    "email-priority-manager config set email.host imap.gmail.com",
                    "email-priority-manager config set ai.model bigmodel"
                ],
                options=[],
                see_also=["getting-started", "email-providers"],
                category="configuration"
            ),
            "email-providers": HelpTopic(
                title="Email Providers",
                description="""
The Email Priority Manager supports various email providers through IMAP.
Each provider has specific configuration requirements.

Supported Providers:
- Gmail: Requires app password (not regular password)
- Outlook: Supports IMAP with standard authentication
- Yahoo: Requires app password for third-party access
- Custom IMAP: Any IMAP-compliant email server
                """,
                examples=[
                    "email-priority-manager config set email.provider gmail",
                    "email-priority-manager config set email.user your_email@gmail.com",
                    "email-priority-manager config set email.password your_app_password"
                ],
                options=[],
                see_also=["configuration", "security"],
                category="configuration"
            ),
            "security": HelpTopic(
                title="Security",
                description="""
Security is a top priority for the Email Priority Manager. Here are the key
security features and best practices:

Security Features:
- Configuration files are stored with restricted permissions
- Email passwords are encrypted at rest
- No email content is sent to external services without explicit consent
- AI model interactions are logged and auditable
- Local database storage with optional encryption

Best Practices:
- Use app passwords instead of regular email passwords
- Enable two-factor authentication on your email account
- Regularly update the application to get security patches
- Review AI model permissions and data usage policies
                """,
                examples=[],
                options=[],
                see_also=["configuration", "ai-models"],
                category="security"
            ),
            "ai-models": HelpTopic(
                title="AI Models",
                description="""
The Email Priority Manager uses AI models to classify emails and determine
priority. You can choose from different models based on your needs.

Available Models:
- bigmodel: High accuracy model for complex email classification
- fastmodel: Quick classification for large volumes
- localmodel: Privacy-focused local processing (when available)

Model Capabilities:
- Priority classification (urgent, important, normal, low)
- Content categorization (work, personal, promotional, etc.)
- Spam detection
- Action item extraction
- Sentiment analysis
                """,
                examples=[
                    "email-priority-manager classify --model bigmodel",
                    "email-priority-manager config set ai.model fastmodel",
                    "email-priority-manager stats --type ai-performance"
                ],
                options=[],
                see_also=["classification", "security"],
                category="ai"
            ),
            "classification": HelpTopic(
                title="Email Classification",
                description="""
Email classification is the core feature that helps you organize your inbox
automatically using AI-powered analysis.

Classification Categories:
Priority Levels:
- Urgent: Requires immediate attention
- Important: Should be addressed soon
- Normal: Standard priority
- Low: Can be addressed later

Content Types:
- Work: Professional correspondence
- Personal: Personal emails
- Promotional: Marketing and promotional content
- Social: Social media notifications
- Updates: Software updates and notifications
                """,
                examples=[
                    "email-priority-manager classify --all",
                    "email-priority-manager list --priority urgent",
                    "email-priority-manager stats --type classification"
                ],
                options=[],
                see_also=["ai-models", "tags"],
                category="features"
            ),
            "tags": HelpTopic(
                title="Email Tags",
                description="""
Tags help you organize and categorize your emails beyond the automatic
classification. You can create custom tags and apply them to emails.

Tag Features:
- Create custom tags with colors and descriptions
- Apply multiple tags to a single email
- Filter emails by tags
- Automatic tag suggestions based on content
- Bulk tag operations
                """,
                examples=[
                    "email-priority-manager tag create --name project-x --color blue",
                    "email-priority-manager tag add --tag project-x --emails 1,2,3",
                    "email-priority-manager list --tag project-x"
                ],
                options=[],
                see_also=["classification", "search"],
                category="features"
            ),
            "search": HelpTopic(
                title="Search and Filter",
                description="""
The Email Priority Manager provides powerful search and filtering capabilities
to help you find specific emails quickly.

Search Types:
- Natural language search: "emails from john about project deadline"
- Filter-based search: --priority urgent --tag work
- Date range search: --since 2024-01-01 --until 2024-01-31
- Content search: Search within email bodies and subjects
                """,
                examples=[
                    "email-priority-manager list --search 'meeting tomorrow'",
                    "email-priority-manager list --priority urgent --since 2024-01-01",
                    "email-priority-manager list --tag work --limit 10"
                ],
                options=[],
                see_also=["tags", "list-command"],
                category="features"
            ),
            "export": HelpTopic(
                title="Data Export",
                description="""
Export your email data and analysis results in various formats for reporting,
backup, or integration with other tools.

Export Formats:
- JSON: Structured data for programmatic use
- CSV: Spreadsheet-compatible format
- Markdown: Documentation and reports
- HTML: Web-ready reports
                """,
                examples=[
                    "email-priority-manager export --format json --output emails.json",
                    "email-priority-manager export --format csv --tag work --since 2024-01-01",
                    "email-priority-manager export --format markdown --output report.md"
                ],
                options=[],
                see_also=["stats", "list-command"],
                category="data"
            ),
            "troubleshooting": HelpTopic(
                title="Troubleshooting",
                description="""
Common issues and solutions for the Email Priority Manager.

Common Issues:
1. Connection Errors: Check email provider settings and network
2. Authentication Failures: Verify credentials and app passwords
3. Model Errors: Check AI model configuration and API keys
4. Performance Issues: Adjust batch sizes and limits
5. Database Errors: Verify database permissions and disk space

Getting Help:
- Use --verbose flag for detailed error information
- Check logs in ~/.email-priority-manager/logs/
- Run config validate to check configuration
                """,
                examples=[
                    "email-priority-manager --verbose scan",
                    "email-priority-manager config validate",
                    "email-priority-manager stats --type system"
                ],
                options=[],
                see_also=["configuration", "logging"],
                category="support"
            ),
            "logging": HelpTopic(
                title="Logging and Debugging",
                description="""
The Email Priority Manager provides comprehensive logging to help you
understand what's happening and debug issues.

Log Levels:
- DEBUG: Detailed information for debugging
- INFO: General information about operations
- WARNING: Potential issues that need attention
- ERROR: Serious errors that prevent normal operation

Log Files:
- Location: ~/.email-priority-manager/logs/
- Rotation: Daily log files with 30-day retention
- Format: Timestamped with detailed operation information
                """,
                examples=[
                    "email-priority-manager --log-level DEBUG scan",
                    "email-priority-manager --verbose list",
                    "email-priority-manager config set logging.level DEBUG"
                ],
                options=[],
                see_also=["troubleshooting", "configuration"],
                category="support"
            )
        }

        # Set up categories
        self.categories = {
            "basics": ["getting-started"],
            "configuration": ["configuration", "email-providers"],
            "security": ["security"],
            "ai": ["ai-models"],
            "features": ["classification", "tags", "search"],
            "data": ["export"],
            "support": ["troubleshooting", "logging"]
        }

    def add_topic(self, topic_id: str, topic: HelpTopic):
        """Add a help topic."""
        self.topics[topic_id] = topic
        if topic.category not in self.categories:
            self.categories[topic.category] = []
        if topic_id not in self.categories[topic.category]:
            self.categories[topic.category].append(topic_id)

    def add_command_help(self, command_id: str, command_help: CommandHelp):
        """Add command help information."""
        self.commands[command_id] = command_help

    def show_help_overview(self):
        """Show main help overview."""
        # Create title
        title_text = Text()
        title_text.append("Email Priority Manager", style="bold green")
        title_text.append(" - Help System", style="bold blue")

        title_panel = Panel(
            title_text,
            title="Help Overview",
            border_style="blue",
            padding=(1, 2)
        )

        self.console.print(title_panel)
        self.console.print()

        # Show categories
        for category, topic_ids in self.categories.items():
            if category == "commands" and not self.commands:
                continue

            self.console.print(StyledOutput.header(category.title(), 2))

            if category == "commands":
                # Show commands
                for cmd_id, cmd_help in self.commands.items():
                    self.console.print(f"  • {Colors.CYAN}{cmd_help.name}{Colors.RESET}: {cmd_help.description}")
            else:
                # Show topics
                for topic_id in topic_ids:
                    if topic_id in self.topics:
                        topic = self.topics[topic_id]
                        self.console.print(f"  • {Colors.CYAN}{topic.title}{Colors.RESET}: {topic.description[:100]}...")

            self.console.print()

        # Show usage examples
        self.console.print(StyledOutput.header("Common Commands", 2))
        examples = [
            "email-priority-manager --help        Show this help message",
            "email-priority-manager init          Initialize the system",
            "email-priority-manager scan           Scan mailbox for emails",
            "email-priority-manager list           List emails with filters",
            "email-priority-manager config show    Show current configuration",
            "email-priority-manager help topic     Get help on a specific topic"
        ]

        for example in examples:
            self.console.print(f"  {Colors.GRAY}{example}{Colors.RESET}")

        self.console.print()

    def show_topic_help(self, topic_id: str):
        """Show help for a specific topic."""
        if topic_id not in self.topics:
            self.console.print(f"{Colors.RED}Unknown topic: {topic_id}{Colors.RESET}")
            self.console.print(f"Available topics: {', '.join(self.topics.keys())}{Colors.RESET}")
            return

        topic = self.topics[topic_id]

        # Topic title
        title_panel = Panel(
            topic.title,
            title=f"Help: {topic.title}",
            border_style="blue",
            padding=(1, 2)
        )
        self.console.print(title_panel)

        # Description
        self.console.print()
        self.console.print(topic.description.strip())
        self.console.print()

        # Examples
        if topic.examples:
            self.console.print(StyledOutput.header("Examples", 2))
            for example in topic.examples:
                code_syntax = Syntax(example, "bash", theme="monokai", line_numbers=False)
                self.console.print(code_syntax)
            self.console.print()

        # Options
        if topic.options:
            self.console.print(StyledOutput.header("Options", 2))
            options_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
            options_table.add_column("Option", style="cyan")
            options_table.add_column("Description", style="white")

            for option in topic.options:
                options_table.add_row(option.get("option", ""), option.get("description", ""))

            self.console.print(options_table)
            self.console.print()

        # See also
        if topic.see_also:
            self.console.print(StyledOutput.header("See Also", 2))
            for related in topic.see_also:
                if related in self.topics:
                    related_topic = self.topics[related]
                    self.console.print(f"  • {Colors.CYAN}{related_topic.title}{Colors.RESET}: {related_topic.description[:80]}...")
            self.console.print()

    def show_command_help(self, command_id: str):
        """Show help for a specific command."""
        if command_id not in self.commands:
            self.console.print(f"{Colors.RED}Unknown command: {command_id}{Colors.RESET}")
            self.console.print(f"Available commands: {', '.join(self.commands.keys())}{Colors.RESET}")
            return

        command = self.commands[command_id]

        # Command title
        title_panel = Panel(
            command.name,
            title=f"Command: {command.name}",
            border_style="green",
            padding=(1, 2)
        )
        self.console.print(title_panel)

        # Description
        self.console.print()
        self.console.print(command.description)
        self.console.print()

        # Usage
        self.console.print(StyledOutput.header("Usage", 2))
        usage_syntax = Syntax(command.usage, "bash", theme="monokai", line_numbers=False)
        self.console.print(usage_syntax)
        self.console.print()

        # Options
        if command.options:
            self.console.print(StyledOutput.header("Options", 2))
            options_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
            options_table.add_column("Option", style="cyan", width=15)
            options_table.add_column("Description", style="white")

            for option in command.options:
                option_text = option.get("option", "")
                if option.get("short"):
                    option_text += f", {option.get('short')}"
                if option.get("default"):
                    option_text += f" (default: {option.get('default')})"

                options_table.add_row(option_text, option.get("description", ""))

            self.console.print(options_table)
            self.console.print()

        # Examples
        if command.examples:
            self.console.print(StyledOutput.header("Examples", 2))
            for example in command.examples:
                example_syntax = Syntax(example, "bash", theme="monokai", line_numbers=False)
                self.console.print(example_syntax)
            self.console.print()

        # Notes
        if command.notes:
            self.console.print(StyledOutput.header("Notes", 2))
            for note in command.notes:
                self.console.print(f"  • {note}")
            self.console.print()

    def show_all_topics(self):
        """Show all available topics."""
        self.console.print(StyledOutput.header("Available Help Topics", 1))

        for category, topic_ids in self.categories.items():
            if category == "commands":
                continue

            self.console.print(StyledOutput.header(category.title(), 2))
            for topic_id in topic_ids:
                if topic_id in self.topics:
                    topic = self.topics[topic_id]
                    self.console.print(f"  • {Colors.CYAN}{topic.title}{Colors.RESET} ({Colors.GRAY}{topic_id}{Colors.RESET})")
            self.console.print()

    def show_all_commands(self):
        """Show all available commands."""
        if not self.commands:
            self.console.print(f"{Colors.YELLOW}No commands available yet.{Colors.RESET}")
            return

        self.console.print(StyledOutput.header("Available Commands", 1))

        for cmd_id, cmd_help in self.commands.items():
            self.console.print(f"  • {Colors.CYAN}{cmd_help.name}{Colors.RESET}: {cmd_help.description}")

        self.console.print()

    def generate_man_page(self, command_id: Optional[str] = None) -> str:
        """Generate man page content for a command or overview."""
        # This is a simplified version - a full man page generator would be more complex
        if command_id and command_id in self.commands:
            command = self.commands[command_id]
            man_content = f"""
.TH {command.name.upper()} 1 "Email Priority Manager" "User Commands"

.SH NAME
{command.name} \\- {command.description}

.SH SYNOPSIS
.B {command.usage}

.SH DESCRIPTION
{command.description}
"""

            if command.options:
                man_content += "\n.SH OPTIONS\n"
                for option in command.options:
                    man_content += f".TP\n.B {option.get('option', '')}\n{option.get('description', '')}\n"

            if command.examples:
                man_content += "\n.SH EXAMPLES\n"
                for example in command.examples:
                    man_content += f".TP\n.B {example}\n"

            return man_content
        else:
            # Generate overview man page
            return """
.TH EMAIL-PRIORITY-MANAGER 1 "Email Priority Manager" "User Commands"

.SH NAME
email-priority-manager \\- Intelligent email classification and organization tool

.SH SYNOPSIS
.B email-priority-manager
[\\fIOPTIONS\\fR] \\fICOMMAND\\fR [\\fICOMMAND OPTIONS\\fR]

.SH DESCRIPTION
Email Priority Manager is a CLI tool that uses AI to classify and organize
your emails automatically, helping you prioritize important messages and
reduce inbox clutter.

.SH COMMANDS
.TP
.B init
Initialize email database and configuration
.TP
.B scan
Scan mailbox for emails
.TP
.B classify
Process and classify emails
.TP
.B list
Display emails with filters
.TP
.B tag
Manage email tags
.TP
.B config
Manage configuration
.TP
.B export
Export email data
.TP
.B stats
Show statistics and reports

.SH OPTIONS
.TP
.B \\-h, \\-\\-help
Show help message
.TP
.B \\-v, \\-\\-verbose
Enable verbose output
.TP
.B \\-q, \\-\\-quiet
Suppress all output except errors
.TP
.B \\-\\-config\\-file FILE
Path to configuration file
.TP
.B \\-\\-log\\-level LEVEL
Set logging level (DEBUG, INFO, WARNING, ERROR)

.SH EXAMPLES
.TP
.B email-priority-manager init
Initialize the system
.TP
.B email-priority-manager scan \\-\\-limit 50
Scan first 50 emails
.TP
.B email-priority-manager list \\-\\-priority urgent
Show urgent emails only

.SH SEE ALSO
Full documentation is available at: https://github.com/your-repo/email-priority-manager
"""

    def search_help(self, query: str) -> List[str]:
        """Search help topics and commands for matching content."""
        query_lower = query.lower()
        results = []

        # Search topics
        for topic_id, topic in self.topics.items():
            if (query_lower in topic.title.lower() or
                query_lower in topic.description.lower() or
                any(query_lower in example.lower() for example in topic.examples)):
                results.append(f"topic:{topic_id}")

        # Search commands
        for cmd_id, command in self.commands.items():
            if (query_lower in command.name.lower() or
                query_lower in command.description.lower() or
                any(query_lower in example.lower() for example in command.examples)):
                results.append(f"command:{cmd_id}")

        return results


# Global help system instance
_help_system: Optional[HelpSystem] = None


def get_help_system() -> HelpSystem:
    """Get the global help system instance."""
    global _help_system
    if _help_system is None:
        _help_system = HelpSystem()
    return _help_system


def show_help_overview():
    """Show main help overview."""
    help_system = get_help_system()
    help_system.show_help_overview()


def show_topic_help(topic_id: str):
    """Show help for a specific topic."""
    help_system = get_help_system()
    help_system.show_topic_help(topic_id)


def show_command_help(command_id: str):
    """Show help for a specific command."""
    help_system = get_help_system()
    help_system.show_command_help(command_id)


def search_help(query: str) -> List[str]:
    """Search help content."""
    help_system = get_help_system()
    return help_system.search_help(query)