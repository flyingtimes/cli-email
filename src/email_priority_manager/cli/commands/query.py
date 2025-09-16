"""
CLI commands for natural language query interface.

Provides interactive and batch query capabilities for email search
using conversational language and AI-powered understanding.
"""

import logging
from typing import Optional, List
import json
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.text import Text

from ...core.query_interface import QueryProcessor, SearchResult
from ...database.models import EmailModel, PriorityModel
from ...config.settings import Settings


console = Console()


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--no-ai', is_flag=True, help='Disable AI enhancements')
@click.pass_context
def query(ctx, config, verbose, no_ai):
    """Natural language query interface for email search."""
    ctx.ensure_object(dict)

    # Initialize settings
    settings = Settings()
    if config:
        from pathlib import Path
        settings = Settings.from_config_file(Path(config))

    ctx.obj['settings'] = settings
    ctx.obj['verbose'] = verbose
    ctx.obj['use_ai'] = not no_ai

    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console.print("[bold green]Email Priority Manager - Natural Language Query Interface[/bold green]")


@query.command()
@click.argument('query_text', required=False)
@click.option('--limit', '-l', default=50, help='Maximum number of results')
@click.option('--output', '-o', type=click.Choice(['table', 'json', 'summary']), default='table', help='Output format')
@click.option('--save', '-s', help='Save results to file')
@click.pass_context
def search(ctx, query_text, limit, output, save):
    """Search emails using natural language query."""
    settings = ctx.obj['settings']
    verbose = ctx.obj['verbose']
    use_ai = ctx.obj['use_ai']

    # Get query text interactively if not provided
    if not query_text:
        query_text = Prompt.ask("[bold blue]Enter your search query[/bold blue]")

    if not query_text:
        console.print("[red]Error: No query provided[/red]")
        return

    # Initialize query processor
    from ...database.models import DatabaseManager
    db_manager = DatabaseManager(settings.database.path)
    session = db_manager.get_session()
    query_processor = QueryProcessor(settings, session)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Processing query...", total=None)

            # Process query
            result = query_processor.process_query(query_text, use_ai=use_ai)
            result.query_parameters.limit = limit  # Apply user limit

        # Display results
        if output == 'table':
            _display_results_table(result, verbose)
        elif output == 'json':
            _display_results_json(result)
        elif output == 'summary':
            _display_results_summary(result)

        # Show suggestions
        if result.suggested_followups:
            console.print("\n[bold cyan]Suggested follow-up queries:[/bold cyan]")
            for i, suggestion in enumerate(result.suggested_followups, 1):
                console.print(f"  {i}. {suggestion}")

        # Save results if requested
        if save:
            _save_results(result, save)

        # Show performance metrics
        if verbose:
            console.print(f"\n[dim]Query processed in {result.processing_time:.2f}s[/dim]")
            console.print(f"[dim]Found {result.total_count} results (showing {len(result.emails)})[/dim]")
            console.print(f"[dim]AI enhanced: {result.ai_enhanced}[/dim]")

    except Exception as e:
        console.print(f"[red]Error processing query: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
    finally:
        session.close()


@query.command()
@click.option('--limit', '-l', default=50, help='Maximum number of results')
@click.option('--output', '-o', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def recent(ctx, limit, output):
    """Show recent emails."""
    settings = ctx.obj['settings']
    verbose = ctx.obj['verbose']
    use_ai = ctx.obj['use_ai']

    # Initialize query processor
    from ...database.models import DatabaseManager
    db_manager = DatabaseManager(settings.database.path)
    session = db_manager.get_session()
    query_processor = QueryProcessor(settings, session)

    try:
        # Search for recent emails
        result = query_processor.process_query("emails from today", use_ai=use_ai)
        result.query_parameters.limit = limit

        if output == 'table':
            _display_results_table(result, verbose)
        elif output == 'json':
            _display_results_json(result)

    except Exception as e:
        console.print(f"[red]Error retrieving recent emails: {e}[/red]")
    finally:
        session.close()


@query.command()
@click.pass_context
def interactive(ctx):
    """Start interactive query session."""
    settings = ctx.obj['settings']
    verbose = ctx.obj['verbose']
    use_ai = ctx.obj['use_ai']

    console.print("[bold green]Interactive Email Search[/bold green]")
    console.print("Type your queries in natural language. Type 'exit' or 'quit' to stop.\n")

    # Initialize query processor
    from ...database.models import DatabaseManager
    db_manager = DatabaseManager(settings.database.path)
    session = db_manager.get_session()
    query_processor = QueryProcessor(settings, session)

    try:
        while True:
            query_text = Prompt.ask("[bold blue]Search for[/bold blue]")

            if query_text.lower() in ['exit', 'quit']:
                console.print("[yellow]Goodbye![/yellow]")
                break

            if not query_text.strip():
                continue

            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task("Processing query...", total=None)
                    result = query_processor.process_query(query_text, use_ai=use_ai)

                # Display results
                _display_results_summary(result)

                # Show follow-up suggestions
                if result.suggested_followups:
                    console.print("\n[dim]You might also want to try:[/dim]")
                    for suggestion in result.suggested_followups[:3]:
                        console.print(f"  • {suggestion}")

                console.print()  # Empty line for readability

            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
    finally:
        session.close()


@query.command()
@click.argument('partial_query', required=False)
@click.option('--limit', '-l', default=20, help='Maximum number of suggestions')
@click.pass_context
def suggest(ctx, partial_query, limit):
    """Get query suggestions based on partial input."""
    settings = ctx.obj['settings']

    # Initialize query processor
    from ...database.models import DatabaseManager
    db_manager = DatabaseManager(settings.database.path)
    session = db_manager.get_session()
    query_processor = QueryProcessor(settings, session)

    try:
        suggestions = query_processor.get_query_suggestions(partial_query or "")

        if suggestions:
            console.print("[bold cyan]Query suggestions:[/bold cyan]")
            for i, suggestion in enumerate(suggestions[:limit], 1):
                console.print(f"  {i}. {suggestion}")
        else:
            console.print("[yellow]No suggestions found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error getting suggestions: {e}[/red]")
    finally:
        session.close()


@query.command()
@click.pass_context
def stats(ctx):
    """Show search statistics and performance metrics."""
    settings = ctx.obj['settings']

    # Initialize query processor
    from ...database.models import DatabaseManager
    db_manager = DatabaseManager(settings.database.path)
    session = db_manager.get_session()
    query_processor = QueryProcessor(settings, session)

    try:
        stats = query_processor.get_search_stats()

        # Create stats table
        table = Table(title="Search Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Cache Size", str(stats['cache_size']))
        table.add_row("Cache TTL", f"{stats['cache_ttl']} seconds")
        table.add_row("Search Patterns", str(stats['search_patterns']))
        table.add_row("AI Available", "Yes" if stats['ai_available'] else "No")
        table.add_row("Total Queries Processed", str(stats['total_queries_processed']))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error getting stats: {e}[/red]")
    finally:
        session.close()


@query.command()
@click.pass_context
def clear_cache(ctx):
    """Clear query cache."""
    settings = ctx.obj['settings']

    # Initialize query processor
    from ...database.models import DatabaseManager
    db_manager = DatabaseManager(settings.database.path)
    session = db_manager.get_session()
    query_processor = QueryProcessor(settings, session)

    try:
        cache_size = len(query_processor.query_cache)
        query_processor.clear_cache()
        console.print(f"[green]Cleared {cache_size} cached queries[/green]")
    except Exception as e:
        console.print(f"[red]Error clearing cache: {e}[/red]")
    finally:
        session.close()


def _display_results_table(result: SearchResult, verbose: bool):
    """Display search results in table format."""
    if not result.emails:
        console.print("[yellow]No emails found matching your query[/yellow]")
        return

    # Create table
    table = Table(title=f"Search Results ({len(result.emails)} emails)")
    table.add_column("ID", style="dim", width=8)
    table.add_column("Subject", style="bold", width=40)
    table.add_column("Sender", width=25)
    table.add_column("Date", width=12)
    table.add_column("Priority", width=10)
    table.add_column("Score", width=6)

    for email in result.emails:
        # Truncate long subjects
        subject = email['subject'][:40] + "..." if len(email['subject']) > 40 else email['subject']
        sender = email['sender'][:25] + "..." if len(email['sender']) > 25 else email['sender']
        date = datetime.fromisoformat(email['date_received']).strftime('%m/%d')
        priority = email['priority']
        score = f"{result.relevance_scores.get(email['id'], 0):.2f}"

        # Color code priority
        priority_style = {
            'urgent': 'red',
            'high': 'yellow',
            'medium': 'blue',
            'low': 'green'
        }.get(priority, 'white')

        table.add_row(
            str(email['id']),
            subject,
            sender,
            date,
            f"[{priority_style}]{priority}[/{priority_style}]",
            score
        )

    console.print(table)

    # Show query summary if available
    if result.query_summary:
        console.print(Panel(result.query_summary, title="Summary", border_style="blue"))


def _display_results_json(result: SearchResult):
    """Display search results in JSON format."""
    output_data = {
        "query_parameters": {
            "keywords": result.query_parameters.keywords,
            "sender": result.query_parameters.sender,
            "date_from": result.query_parameters.date_from.isoformat() if result.query_parameters.date_from else None,
            "date_to": result.query_parameters.date_to.isoformat() if result.query_parameters.date_to else None,
            "priority": result.query_parameters.priority,
            "has_attachments": result.query_parameters.has_attachments,
            "limit": result.query_parameters.limit,
            "confidence": result.query_parameters.confidence
        },
        "results": result.emails,
        "total_count": result.total_count,
        "processing_time": result.processing_time,
        "ai_enhanced": result.ai_enhanced,
        "query_summary": result.query_summary,
        "suggested_followups": result.suggested_followups
    }

    console.print(json.dumps(output_data, indent=2, default=str))


def _display_results_summary(result: SearchResult):
    """Display search results in summary format."""
    if not result.emails:
        console.print("[yellow]No emails found matching your query[/yellow]")
        return

    # Basic summary
    console.print(f"[bold green]Found {len(result.emails)} emails[/bold green]")

    # Date range
    if result.emails:
        dates = [datetime.fromisoformat(email['date_received']) for email in result.emails]
        oldest = min(dates).strftime('%Y-%m-%d')
        newest = max(dates).strftime('%Y-%m-%d')
        console.print(f"[dim]Date range: {oldest} to {newest}[/dim]")

    # Priority distribution
    priority_counts = {}
    for email in result.emails:
        priority = email['priority']
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

    if priority_counts:
        console.print("\n[bold cyan]Priority distribution:[/bold cyan]")
        for priority, count in priority_counts.items():
            console.print(f"  {priority}: {count}")

    # Top senders
    senders = {}
    for email in result.emails:
        sender = email['sender']
        senders[sender] = senders.get(sender, 0) + 1

    if senders:
        top_senders = sorted(senders.items(), key=lambda x: x[1], reverse=True)[:3]
        console.print("\n[bold cyan]Top senders:[/bold cyan]")
        for sender, count in top_senders:
            console.print(f"  {sender}: {count}")

    # Show AI summary if available
    if result.query_summary:
        console.print(f"\n[bold blue]AI Summary:[/bold blue]")
        console.print(result.query_summary)

    # Show top results
    console.print(f"\n[bold green]Top results:[/bold green]")
    for i, email in enumerate(result.emails[:20], 1):
        score = result.relevance_scores.get(email['id'], 0)
        console.print(f"\n{i}. [bold]{email['subject']}[/bold] ({score:.2f})")
        console.print(f"   From: {email['sender']}")
        console.print(f"   Date: {datetime.fromisoformat(email['date_received']).strftime('%Y-%m-%d %H:%M')}")
        console.print(f"   Priority: {email['priority']}")


def _save_results(result: SearchResult, filename: str):
    """Save search results to file."""
    try:
        output_data = {
            "query": result.query_parameters.__dict__,
            "results": result.emails,
            "total_count": result.total_count,
            "processing_time": result.processing_time,
            "ai_enhanced": result.ai_enhanced,
            "query_summary": result.query_summary,
            "suggested_followups": result.suggested_followups,
            "saved_at": datetime.now().isoformat()
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, default=str, ensure_ascii=False)

        console.print(f"[green]Results saved to {filename}[/green]")

    except Exception as e:
        console.print(f"[red]Error saving results: {e}[/red]")


if __name__ == '__main__':
    query()