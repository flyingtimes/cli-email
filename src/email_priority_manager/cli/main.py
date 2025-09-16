"""
主CLI入口点

本模块为邮件优先级管理器CLI应用程序提供主入口点。
它使用Click作为CLI框架，提供强大的命令结构和
全面的帮助系统以及可扩展的架构。
"""

import sys
import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .framework.setup import setup_cli_framework
from .utils.colors import Colors
from .utils.logging import setup_cli_logging
from .utils.prompts import confirm_action
from .commands.help import register_help_command, setup_command_help
from .commands.email import email as email_commands
from .commands.query import query as query_commands
from .commands.setup import setup as setup_commands
from .commands.scan import scan as scan_commands
from .commands.classify import classify as classify_commands
from .commands.list_emails import list_emails_group as list_commands
from .commands.misc_commands import tag, config, export, stats


# Initialize rich console for enhanced output
console = Console()


# Main CLI group
@click.group(
    name="email-priority-manager",
    help="邮件优先级管理器 - 智能邮件分类和组织工具",
    context_settings={"help_option_names": ["-h", "--help"]}
)
@click.version_option(
    version="0.1.0",
    prog_name="邮件优先级管理器",
    message="%(prog)s 版本 %(version)s"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="启用详细输出"
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="禁止所有输出，仅显示错误"
)
@click.option(
    "--config-file",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="配置文件路径"
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="设置日志级别"
)
@click.pass_context
def cli(ctx, verbose, quiet, config_file, log_level):
    """
    邮件优先级管理器 - 智能邮件分类和组织工具

    此CLI提供全面的邮件管理工具，具有AI驱动的
    分类、优先级评估和组织能力。
    """
    # Set up context for command execution
    ctx.ensure_object(dict)

    # Store CLI options in context
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["config_file"] = config_file
    ctx.obj["log_level"] = log_level

    # Set up logging
    if quiet:
        ctx.obj["log_level"] = "ERROR"
    elif verbose:
        ctx.obj["log_level"] = "DEBUG"

    # Initialize CLI framework
    setup_cli_framework(ctx.obj)

    # Set up logging
    setup_cli_logging(ctx.obj["log_level"])

    # Display welcome message if no command provided
    if len(sys.argv) == 1:
        display_welcome_message()


def display_welcome_message():
    """显示欢迎消息和基本使用信息。"""
    welcome_text = Text()
    welcome_text.append("欢迎使用 ", style="bold blue")
    welcome_text.append("邮件优先级管理器", style="bold green")
    welcome_text.append("！", style="bold blue")

    panel = Panel(
        welcome_text,
        title="邮件优先级管理器 v0.1.0",
        border_style="blue",
        padding=(1, 2)
    )

    console.print(panel)
    console.print()

    # 显示快速开始信息
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("命令", style="cyan", width=15)
    table.add_column("描述", style="white")

    table.add_row("init", "初始化邮件数据库和配置")
    table.add_row("scan", "扫描邮箱邮件")
    table.add_row("classify", "处理和分类邮件")
    table.add_row("list", "显示带过滤器的邮件")
    table.add_row("query search", "使用自然语言搜索邮件")
    table.add_row("query interactive", "交互式邮件搜索会话")
    table.add_row("tag", "管理邮件标签")
    table.add_row("config", "管理配置")
    table.add_row("export", "导出邮件数据")
    table.add_row("stats", "显示统计和报告")

    console.print(table)
    console.print()
    console.print(f"{Colors.YELLOW}使用 --help 获取详细使用信息{Colors.RESET}")


# Command groups for better organization
@cli.group(
    name="setup",
    help="Setup and configuration commands"
)
def setup_group():
    """Setup and configuration commands."""
    pass


@cli.group(
    name="email",
    help="Email processing and management commands"
)
def email_group():
    """Email processing and management commands."""
    pass


@cli.group(
    name="query",
    help="Query and display commands"
)
def query_group():
    """Query and display commands."""
    pass


@cli.group(
    name="data",
    help="Data management and export commands"
)
def data_group():
    """Data management and export commands."""
    pass


# 错误处理和验证
def handle_cli_error(error, exit_code=1):
    """处理CLI错误并提供用户友好的消息。"""
    if isinstance(error, click.ClickException):
        console.print(f"{Colors.RED}错误：{error.message}{Colors.RESET}")
    else:
        console.print(f"{Colors.RED}未知错误：{str(error)}{Colors.RESET}")

    sys.exit(exit_code)


# 添加命令组
cli.add_command(setup_commands)
cli.add_command(email_commands)
cli.add_command(query_commands)
cli.add_command(scan_commands)
cli.add_command(classify_commands)
cli.add_command(list_commands)
cli.add_command(tag)
cli.add_command(config)
cli.add_command(export)
cli.add_command(stats)

# 从setup组添加直接命令以便更轻松访问
from .commands.setup import init_command, config_command, database_command, secrets_command, status_command
from .commands.scan import scan_mailbox, scan_quick, scan_full, scan_status
from .commands.classify import classify_emails, classify_batch, classify_reclassify, classify_stats
from .commands.list_emails import list_emails, list_urgent, list_unread, list_recent, list_by_sender, list_search

@cli.command(
    name="init",
    help="初始化邮件数据库和配置",
    short_help="初始化系统"
)
@click.option(
    "--config-path",
    type=click.Path(),
    default=None,
    help="配置文件路径"
)
@click.option(
    "--database-path",
    type=click.Path(),
    default=None,
    help="数据库文件路径"
)
@click.option(
    "--force",
    is_flag=True,
    help="强制初始化，即使已经配置过"
)
@click.pass_context
def init_direct(ctx, config_path, database_path, force):
    """初始化邮件数据库和配置。"""
    # 转发到setup init命令
    ctx.invoke(init_command, config_path=config_path, database_path=database_path, force=force)


@cli.command(
    name="scan",
    help="扫描邮箱邮件",
    short_help="扫描邮箱"
)
@click.option(
    "--limit", "-l",
    type=int,
    default=100,
    help="最大扫描邮件数量"
)
@click.option(
    "--folder", "-f",
    default="INBOX",
    help="扫描的邮件文件夹"
)
@click.option(
    "--unread-only", "-u",
    is_flag=True,
    help="仅扫描未读邮件"
)
@click.option(
    "--since-days", "-s",
    type=int,
    help="扫描最近N天的邮件"
)
@click.option(
    "--classify", "-c",
    is_flag=True,
    help="扫描后分类邮件"
)
@click.option(
    "--output-format", "-o",
    type=click.Choice(["table", "json", "summary"]),
    default="table",
    help="输出格式"
)
@click.pass_context
def scan_direct(ctx, limit, folder, unread_only, since_days, classify, output_format):
    """扫描邮箱邮件。"""
    # 转发到scan mailbox命令
    ctx.invoke(scan_mailbox, limit=limit, folder=folder, unread_only=unread_only,
               since_days=since_days, classify=classify, save_to_db=True, output_format=output_format)


@cli.command(
    name="classify",
    help="处理和分类邮件",
    short_help="分类邮件"
)
@click.option(
    "--limit", "-l",
    type=int,
    default=100,
    help="最大分类邮件数量"
)
@click.option(
    "--unclassified-only", "-u",
    is_flag=True,
    help="仅分类未分类的邮件"
)
@click.option(
    "--folder", "-f",
    default="INBOX",
    help="按邮件文件夹过滤"
)
@click.option(
    "--since-days", "-s",
    type=int,
    help="分类最近N天的邮件"
)
@click.option(
    "--priority-filter",
    type=click.Choice(["urgent", "high", "medium", "low"]),
    help="按优先级过滤"
)
@click.option(
    "--output-format", "-o",
    type=click.Choice(["table", "json", "summary"]),
    default="table",
    help="输出格式"
)
@click.pass_context
def classify_direct(ctx, limit, unclassified_only, folder, since_days, priority_filter, output_format):
    """处理和分类邮件。"""
    # 转发到classify emails命令
    ctx.invoke(classify_emails, limit=limit, unclassified_only=unclassified_only, folder=folder,
               since_days=since_days, priority_filter=priority_filter, output_format=output_format)


@cli.command(
    name="list",
    help="显示带过滤器的邮件",
    short_help="列出邮件"
)
@click.option(
    "--limit", "-l",
    type=int,
    default=50,
    help="最大显示邮件数量"
)
@click.option(
    "--priority", "-p",
    type=click.Choice(["urgent", "high", "medium", "low"]),
    help="按优先级过滤"
)
@click.option(
    "--category", "-c",
    help="按分类过滤"
)
@click.option(
    "--sender", "-s",
    help="按发件人过滤（部分匹配）"
)
@click.option(
    "--subject", "-S",
    help="按主题过滤（部分匹配）"
)
@click.option(
    "--unread-only", "-u",
    is_flag=True,
    help="仅显示未读邮件"
)
@click.option(
    "--since-days", "-d",
    type=int,
    help="显示最近N天的邮件"
)
@click.option(
    "--output-format", "-o",
    type=click.Choice(["table", "json", "detailed"]),
    default="table",
    help="输出格式"
)
@click.pass_context
def list_direct(ctx, limit, priority, category, sender, subject, unread_only, since_days, output_format):
    """显示带过滤器的邮件。"""
    # 转发到list emails命令
    ctx.invoke(list_emails, limit=limit, priority=priority, category=category, sender=sender,
               subject=subject, unread_only=unread_only, since_days=since_days, output_format=output_format)

# 主入口点
# 设置帮助系统
setup_command_help()
register_help_command(cli)


def main():
    """CLI应用程序的主入口点。"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print(f"\n{Colors.YELLOW}操作被用户取消。{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        handle_cli_error(e)


if __name__ == "__main__":
    main()