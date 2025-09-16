"""
帮助命令实现

本模块为邮件优先级管理器CLI提供帮助命令。
"""

import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..framework.help import get_help_system, show_help_overview, show_topic_help, show_command_help, search_help, CommandHelp
from ..utils.colors import Colors, StyledOutput
from ..base import with_context, CommandContext


console = Console()


@click.command(
    name="help",
    help="显示帮助信息和文档"
)
@click.argument(
    "topic",
    required=False,
    default=None
)
@click.option(
    "--search",
    "-s",
    help="搜索帮助主题"
)
@click.option(
    "--list-topics",
    is_flag=True,
    help="列出所有可用的帮助主题"
)
@click.option(
    "--list-commands",
    is_flag=True,
    help="列出所有可用的命令"
)
@click.option(
    "--format",
    type=click.Choice(["text", "markdown"]),
    default="text",
    help="帮助内容的输出格式"
)
@with_context
def help_command(
    cmd_ctx: CommandContext,
    topic: Optional[str],
    search: Optional[str],
    list_topics: bool,
    list_commands: bool,
    format: str
):
    """
    显示邮件优先级管理器的综合帮助信息。

    使用此命令获取特定主题的帮助，搜索信息，
    或浏览完整的帮助系统。
    """
    help_system = get_help_system()

    try:
        if search:
            # 搜索功能
            results = search_help(search)
            if results:
                cmd_ctx.success(f"为'{search}'找到{len(results)}个结果：")
                console.print()

                for result in results:
                    result_type, result_id = result.split(":", 1)
                    if result_type == "topic":
                        topic = help_system.topics.get(result_id)
                        if topic:
                            console.print(f"  • {Colors.CYAN}{topic.title}{Colors.RESET} ({Colors.GRAY}{result_id}{Colors.RESET})")
                            console.print(f"    {topic.description[:80]}...")
                    elif result_type == "command":
                        command = help_system.commands.get(result_id)
                        if command:
                            console.print(f"  • {Colors.GREEN}{command.name}{Colors.RESET} ({Colors.GRAY}{result_id}{Colors.RESET})")
                            console.print(f"    {command.description[:80]}...")

                console.print()
                cmd_ctx.info("使用'email-priority-manager help <主题|命令>'获取详细信息。")
            else:
                cmd_ctx.warning(f"未找到'{search}'的结果")
                cmd_ctx.info("使用--list-topics查看可用主题。")

        elif list_topics:
            # 列出所有主题
            help_system.show_all_topics()

        elif list_commands:
            # 列出所有命令
            help_system.show_all_commands()

        elif topic:
            # 显示特定主题或命令帮助
            if topic in help_system.topics:
                show_topic_help(topic)
            elif topic in help_system.commands:
                show_command_help(topic)
            else:
                # 尝试找到部分匹配
                topic_matches = [tid for tid in help_system.topics.keys() if topic in tid]
                command_matches = [cid for cid in help_system.commands.keys() if topic in cid]

                if topic_matches or command_matches:
                    cmd_ctx.warning(f"未找到主题'{topic}'。您是想找：")
                    if topic_matches:
                        cmd_ctx.info("主题：")
                        for match in topic_matches:
                            cmd_ctx.info(f"  • {match}")
                    if command_matches:
                        cmd_ctx.info("命令：")
                        for match in command_matches:
                            cmd_ctx.info(f"  • {match}")
                else:
                    cmd_ctx.error(f"未找到主题'{topic}'")
                    cmd_ctx.info("使用--list-topics查看可用主题。")
                    sys.exit(1)

        else:
            # 显示主要帮助概览
            show_help_overview()

    except Exception as e:
        cmd_ctx.error(f"显示帮助时出错：{str(e)}")
        if cmd_ctx.verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


# 注册帮助命令
def register_help_command(cli_group):
    """向CLI组注册帮助命令。"""
    cli_group.add_command(help_command)


# 添加命令帮助信息
def setup_command_help():
    """为内置命令设置帮助信息。"""
    help_system = get_help_system()

    # 添加主CLI帮助
    help_system.add_command_help(
        "main",
        CommandHelp(
            name="email-priority-manager",
            description="邮件管理的主要CLI入口点",
            usage="email-priority-manager [选项] 命令 [参数]",
            options=[
                {
                    "option": "--verbose, -v",
                    "description": "启用详细输出"
                },
                {
                    "option": "--quiet, -q",
                    "description": "禁止除错误外的所有输出"
                },
                {
                    "option": "--config-file 文件",
                    "description": "配置文件路径"
                },
                {
                    "option": "--log-level 级别",
                    "description": "设置日志级别（DEBUG, INFO, WARNING, ERROR）"
                },
                {
                    "option": "--help, -h",
                    "description": "显示帮助信息"
                }
            ],
            examples=[
                "email-priority-manager --verbose",
                "email-priority-manager --config-file custom-config.yaml scan",
                "email-priority-manager --log-level DEBUG classify"
            ],
            notes=[
                "在任何命令后使用--help查看命令特定帮助",
                "配置文件是可选的 - 如果未提供系统将使用默认值",
                "日志级别控制操作期间的输出详细程度"
            ],
            category="main"
        )
    )

    # 添加帮助命令本身的帮助
    help_system.add_command_help(
        "help",
        CommandHelp(
            name="help",
            description="显示帮助信息和文档",
            usage="email-priority-manager help [主题] [选项]",
            options=[
                {
                    "option": "--search, -s 文本",
                    "description": "搜索帮助主题"
                },
                {
                    "option": "--list-topics",
                    "description": "列出所有可用的帮助主题"
                },
                {
                    "option": "--list-commands",
                    "description": "列出所有可用的命令"
                },
                {
                    "option": "--format 格式",
                    "description": "输出格式（text, markdown）"
                }
            ],
            examples=[
                "email-priority-manager help",
                "email-priority-manager help getting-started",
                "email-priority-manager help --search classification",
                "email-priority-manager help --list-topics"
            ],
            notes=[
                "帮助主题涵盖概念、功能和故障排除",
                "使用--search快速找到相关的帮助内容",
                "命令帮助显示使用示例和选项"
            ],
            category="help"
        )
    )