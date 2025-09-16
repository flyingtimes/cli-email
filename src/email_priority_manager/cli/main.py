"""
Main CLI entry point for Email Priority Manager.

Provides command-line interface for email management, configuration,
and system administration.
"""

import click
import sys
from pathlib import Path

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from email_priority_manager.config.settings import (
    get_settings,
    validate_configuration,
    create_default_config_file
)
from email_priority_manager.config.secrets import (
    setup_email_interactive,
    setup_ai_interactive,
    get_secrets_manager
)
from email_priority_manager.utils.logger import configure_logging, get_logger

logger = get_logger(__name__)


@click.group()
@click.option('--config-dir', '-c', default=None, help='Configuration directory')
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, config_dir, debug, verbose):
    """Email Priority Manager - AI-powered email management system."""
    ctx.ensure_object(dict)

    # Initialize context
    ctx.obj['config_dir'] = config_dir
    ctx.obj['debug'] = debug
    ctx.obj['verbose'] = verbose

    # Configure logging early
    try:
        settings = get_settings(config_dir)
        if debug:
            settings.logging.level = "DEBUG"
        configure_logging(settings)
    except Exception:
        # Use basic logging if configuration fails
        import logging
        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

    logger.debug("CLI initialized", extra={
        'config_dir': config_dir,
        'debug': debug,
        'verbose': verbose
    })


@cli.command()
@click.option('--create-default', is_flag=True, help='Create default configuration file')
@click.pass_context
def setup(ctx, create_default):
    """Interactive setup for Email Priority Manager."""
    logger.info("Starting interactive setup")

    try:
        if create_default:
            config_dir = ctx.obj.get('config_dir', 'config')
            create_default_config_file(config_dir)
            click.echo("✓ Default configuration file created")

        # Setup email configuration
        if click.confirm("Would you like to configure email settings?"):
            if setup_email_interactive():
                click.echo("✓ Email configuration completed")
            else:
                click.echo("✗ Email configuration failed")
                sys.exit(1)

        # Setup AI configuration
        if click.confirm("Would you like to configure AI service settings?"):
            if setup_ai_interactive():
                click.echo("✓ AI service configuration completed")
            else:
                click.echo("✗ AI service configuration failed")
                sys.exit(1)

        # Validate configuration
        if validate_configuration():
            click.echo("✓ Configuration validation passed")
        else:
            click.echo("⚠️  Configuration validation failed - please check your settings")

        click.echo("\nSetup completed successfully!")
        click.echo("You can now run 'email-priority-manager --help' to see available commands.")

    except Exception as e:
        logger.error("Setup failed", error=str(e))
        click.echo(f"✗ Setup failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def validate(ctx):
    """Validate current configuration."""
    logger.info("Validating configuration")

    try:
        config_dir = ctx.obj.get('config_dir')
        if validate_configuration():
            click.echo("✓ Configuration is valid")
        else:
            click.echo("✗ Configuration is invalid")
            sys.exit(1)

    except Exception as e:
        logger.error("Configuration validation failed", error=str(e))
        click.echo(f"✗ Configuration validation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status and configuration."""
    logger.info("Checking system status")

    try:
        config_dir = ctx.obj.get('config_dir')
        settings = get_settings(config_dir)

        click.echo("Email Priority Manager Status")
        click.echo("=" * 40)

        # Basic info
        click.echo(f"Environment: {settings.environment}")
        click.echo(f"Debug Mode: {settings.debug}")
        click.echo(f"Version: {getattr(settings, 'version', '0.1.0')}")

        # Configuration status
        click.echo(f"\nConfiguration:")
        click.echo(f"  Config Directory: {config_dir or 'default'}")
        click.echo(f"  Data Directory: {settings.data_dir}")
        click.echo(f"  Log Directory: {settings.log_dir}")

        # Database status
        db_path = Path(settings.database.path)
        db_exists = db_path.exists()
        click.echo(f"  Database: {settings.database.path} ({'✓' if db_exists else '✗'})")

        # Email configuration
        email_configured = bool(settings.email)
        click.echo(f"  Email Configured: {'✓' if email_configured else '✗'}")

        # AI configuration
        ai_configured = bool(settings.ai)
        click.echo(f"  AI Configured: {'✓' if ai_configured else '✗'}")

        # Secrets status
        try:
            secrets_manager = get_secrets_manager()
            secrets_count = len(secrets_manager.list_secrets())
            click.echo(f"  Secrets Stored: {secrets_count}")
        except Exception:
            click.echo("  Secrets: ✗")

    except Exception as e:
        logger.error("Status check failed", error=str(e))
        click.echo(f"✗ Status check failed: {e}", err=True)
        sys.exit(1)


@cli.group()
def config():
    """Configuration management commands."""
    pass


@config.command()
@click.option('--category', '-c', default=None, help='Filter by category')
@click.pass_context
def list_secrets(ctx, category):
    """List stored secrets."""
    logger.info("Listing secrets")

    try:
        secrets_manager = get_secrets_manager()
        secrets = secrets_manager.list_secrets(category)

        if not secrets:
            click.echo("No secrets found")
            return

        click.echo("Stored Secrets:")
        click.echo("=" * 40)

        for cat, keys in secrets.items():
            click.echo(f"\n{cat}:")
            for key in keys:
                click.echo(f"  - {key}")

    except Exception as e:
        logger.error("Failed to list secrets", error=str(e))
        click.echo(f"✗ Failed to list secrets: {e}", err=True)
        sys.exit(1)


@config.command()
@click.argument('key')
@click.argument('value')
@click.option('--category', '-c', default='general', help='Secret category')
@click.pass_context
def store_secret(ctx, key, value, category):
    """Store a secret."""
    logger.info(f"Storing secret: {key}")

    try:
        secrets_manager = get_secrets_manager()
        secrets_manager.store_secret(key, value, category)
        click.echo(f"✓ Secret '{key}' stored in category '{category}'")

    except Exception as e:
        logger.error("Failed to store secret", error=str(e))
        click.echo(f"✗ Failed to store secret: {e}", err=True)
        sys.exit(1)


@config.command()
@click.argument('key')
@click.option('--category', '-c', default='general', help='Secret category')
@click.pass_context
def delete_secret(ctx, key, category):
    """Delete a secret."""
    logger.info(f"Deleting secret: {key}")

    try:
        secrets_manager = get_secrets_manager()
        secrets_manager.delete_secret(key, category)
        click.echo(f"✓ Secret '{key}' deleted from category '{category}'")

    except Exception as e:
        logger.error("Failed to delete secret", error=str(e))
        click.echo(f"✗ Failed to delete secret: {e}", err=True)
        sys.exit(1)


@cli.group()
def test():
    """Testing and development commands."""
    pass


@test.command()
def unit():
    """Run unit tests."""
    logger.info("Running unit tests")
    os.system("pytest tests/unit/ -v")


@test.command()
def integration():
    """Run integration tests."""
    logger.info("Running integration tests")
    os.system("pytest tests/integration/ -v")


@test.command()
def all():
    """Run all tests."""
    logger.info("Running all tests")
    os.system("pytest tests/ -v --cov=src/email_priority_manager")


def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected error", error=str(e))
        click.echo(f"✗ Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()