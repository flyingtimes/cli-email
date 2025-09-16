"""
CLI Framework Setup

This module provides the setup function for initializing the CLI framework.
"""

import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..utils.logging import get_logger
from ..utils.colors import Colors


logger = get_logger(__name__)


class CLIFramework:
    """Main CLI framework class."""

    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.commands: Dict[str, Any] = {}
        self.validators: Dict[str, List] = {}
        self.middlewares: List = []

    def initialize(self, context: Dict[str, Any]):
        """Initialize the CLI framework with context."""
        self.config = context

        # Set up basic configuration
        self._setup_default_config()
        self._setup_environment()
        self._setup_dependencies()

        logger.info("CLI Framework initialized")

    def _setup_default_config(self):
        """Set up default configuration values."""
        defaults = {
            "output_format": "table",
            "max_items_per_page": 50,
            "progress_enabled": True,
            "colors_enabled": Colors.supports_color(),
            "confirm_dangerous": True,
            "log_level": "INFO",
            "temp_dir": Path.home() / ".email-priority-manager" / "temp",
            "cache_dir": Path.home() / ".email-priority-manager" / "cache",
        }

        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _setup_environment(self):
        """Set up environment-specific configuration."""
        # Create necessary directories
        for dir_key in ["temp_dir", "cache_dir"]:
            dir_path = self.config.get(dir_key)
            if dir_path:
                dir_path.mkdir(parents=True, exist_ok=True)

        # Set up environment variables
        env_config = {
            "EPM_DEBUG": "debug_mode",
            "EPM_VERBOSE": "verbose",
            "EPM_QUIET": "quiet",
            "EPM_NO_COLOR": "colors_enabled",
            "EPM_CONFIG_FILE": "config_file",
        }

        for env_var, config_key in env_config.items():
            env_value = sys.environ.get(env_var)
            if env_value:
                # Handle boolean values
                if config_key == "colors_enabled":
                    self.config[config_key] = env_value.lower() not in ["true", "1", "yes", "on"]
                elif config_key in ["debug_mode", "verbose", "quiet"]:
                    self.config[config_key] = env_value.lower() in ["true", "1", "yes", "on"]
                else:
                    self.config[config_key] = env_value

    def _setup_dependencies(self):
        """Set up and validate dependencies."""
        required_modules = [
            "click",
            "rich",
            "colorama",
        ]

        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)

        if missing_modules:
            error_msg = f"Missing required modules: {', '.join(missing_modules)}"
            logger.error(error_msg)
            print(f"{Colors.RED}Error: {error_msg}{Colors.RESET}")
            print(f"{Colors.YELLOW}Please install missing dependencies with: pip install {' '.join(missing_modules)}{Colors.RESET}")
            sys.exit(1)

    def register_command(self, name: str, command_func, validators: Optional[List] = None):
        """Register a command with the framework."""
        self.commands[name] = command_func
        if validators:
            self.validators[name] = validators

    def add_middleware(self, middleware_func):
        """Add middleware to the command processing pipeline."""
        self.middlewares.append(middleware_func)

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value

    def validate_command(self, command_name: str, args: Dict[str, Any]) -> bool:
        """Validate command arguments."""
        validators = self.validators.get(command_name, [])
        for validator in validators:
            try:
                validator(args)
            except Exception as e:
                logger.error(f"Validation failed for command {command_name}: {str(e)}")
                return False
        return True


# Global framework instance
_framework_instance: Optional[CLIFramework] = None


def get_framework() -> CLIFramework:
    """Get the global CLI framework instance."""
    global _framework_instance
    if _framework_instance is None:
        _framework_instance = CLIFramework()
    return _framework_instance


def setup_cli_framework(context: Dict[str, Any]) -> CLIFramework:
    """Set up the CLI framework with the given context."""
    framework = get_framework()
    framework.initialize(context)
    return framework


def get_cli_config(key: str, default: Any = None) -> Any:
    """Get CLI configuration value."""
    framework = get_framework()
    return framework.get_config(key, default)


def set_cli_config(key: str, value: Any):
    """Set CLI configuration value."""
    framework = get_framework()
    framework.set_config(key, value)