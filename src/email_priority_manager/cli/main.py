"""
Main CLI entry point for Email Priority Manager.

Provides command-line interface for email processing and configuration management.
"""

import click
import sys
from pathlib import Path

from ..config.settings import Settings
from ..utils.logger import setup_logger
from ..core.processor import EmailProcessor
from ..database.models import DatabaseManager


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True),
              help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose logging')
@click.option('--debug', is_flag=True,
              help='Enable debug mode')
@click.pass_context
def main(ctx, config, verbose, debug):
    """Email Priority Manager - AI-powered email prioritization system."""
    ctx.ensure_object(dict)

    # Set up logging
    log_level = 'DEBUG' if debug else ('INFO' if verbose else 'WARNING')
    setup_logger(level=log_level)

    # Load configuration
    try:
        settings = Settings(config_path=config)
        ctx.obj['settings'] = settings
        ctx.obj['processor'] = EmailProcessor(settings)
        ctx.obj['db'] = DatabaseManager(settings)
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--limit', '-l', type=int, default=100,
              help='Maximum number of emails to process')
@click.option('--dry-run', is_flag=True,
              help='Show what would be processed without making changes')
@click.pass_context
def process(ctx, limit, dry_run):
    """Process emails and assign priorities."""
    try:
        processor = ctx.obj['processor']
        db = ctx.obj['db']

        click.echo(f"Processing up to {limit} emails...")

        if dry_run:
            click.echo("DRY RUN: No changes will be made")

        # Get emails to process
        emails = db.get_unprocessed_emails(limit=limit)

        if not emails:
            click.echo("No emails to process")
            return

        for email in emails:
            try:
                priority = processor.classify_email(email)
                click.echo(f"Email {email.id}: {priority}")

                if not dry_run:
                    db.update_email_priority(email.id, priority)

            except Exception as e:
                click.echo(f"Error processing email {email.id}: {e}", err=True)
                continue

        if not dry_run:
            click.echo(f"Successfully processed {len(emails)} emails")
        else:
            click.echo(f"Would process {len(emails)} emails")

    except Exception as e:
        click.echo(f"Error processing emails: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--email', '-e', required=True,
              help='Email address to test classification')
@click.option('--subject', '-s', required=True,
              help='Email subject to test')
@click.option('--body', '-b', required=True,
              help='Email body to test')
@click.pass_context
def test(ctx, email, subject, body):
    """Test email classification with sample data."""
    try:
        processor = ctx.obj['processor']

        # Create test email object
        from ..database.models import Email
        test_email = Email(
            id='test',
            sender=email,
            subject=subject,
            body=body,
            received_date=None
        )

        # Classify the email
        priority = processor.classify_email(test_email)

        click.echo(f"Test Email Classification:")
        click.echo(f"From: {email}")
        click.echo(f"Subject: {subject}")
        click.echo(f"Body: {body[:100]}...")
        click.echo(f"Priority: {priority}")

    except Exception as e:
        click.echo(f"Error testing classification: {e}", err=True)
        sys.exit(1)


@main.command()
@click.pass_context
def config(ctx):
    """Show current configuration."""
    try:
        settings = ctx.obj['settings']

        click.echo("Current Configuration:")
        click.echo(f"Email Server: {settings.email.server}")
        click.echo(f"Email Port: {settings.email.port}")
        click.echo(f"Email User: {settings.email.username}")
        click.echo(f"Database Path: {settings.database.path}")
        click.echo(f"AI Model: {settings.ai.model}")
        click.echo(f"Debug Mode: {settings.debug}")

    except Exception as e:
        click.echo(f"Error showing configuration: {e}", err=True)
        sys.exit(1)


@main.command()
@click.pass_context
def init(ctx):
    """Initialize the application and database."""
    try:
        db = ctx.obj['db']

        click.echo("Initializing Email Priority Manager...")

        # Initialize database
        db.initialize()

        # Create default configuration
        settings = ctx.obj['settings']
        settings.save_default_config()

        click.echo("Initialization complete!")
        click.echo("You can now configure your email settings.")

    except Exception as e:
        click.echo(f"Error initializing: {e}", err=True)
        sys.exit(1)


@main.command()
@click.pass_context
def status(ctx):
    """Show application status and statistics."""
    try:
        db = ctx.obj['db']

        # Get statistics
        stats = db.get_statistics()

        click.echo("Email Priority Manager Status:")
        click.echo(f"Total Emails: {stats.get('total_emails', 0)}")
        click.echo(f"Processed Emails: {stats.get('processed_emails', 0)}")
        click.echo(f"High Priority: {stats.get('high_priority', 0)}")
        click.echo(f"Medium Priority: {stats.get('medium_priority', 0)}")
        click.echo(f"Low Priority: {stats.get('low_priority', 0)}")

    except Exception as e:
        click.echo(f"Error getting status: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()