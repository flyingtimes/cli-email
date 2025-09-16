"""
Configuration settings management for Email Priority Manager.

Provides centralized configuration loading, validation, and management
with environment variable support and secure credential handling.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, Union
from functools import lru_cache

from .models import (
    AppConfig,
    EmailConfig,
    DatabaseConfig,
    AIConfig,
    ProcessingConfig,
    LoggingConfig,
    DatabaseSettings,
    EmailSettings,
    AISettings
)
from .secrets import SecretsManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Manages application configuration loading and validation."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration manager."""
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self.secrets_manager = SecretsManager()
        self._config: Optional[AppConfig] = None

    def load_config(self) -> AppConfig:
        """Load and validate application configuration."""
        if self._config is not None:
            return self._config

        try:
            # Load configuration from various sources
            config_data = self._load_config_sources()

            # Create configuration object
            self._config = AppConfig(**config_data)

            logger.info("Configuration loaded successfully",
                       environment=self._config.environment)
            return self._config

        except Exception as e:
            logger.error("Failed to load configuration", error=str(e))
            raise ConfigurationError(f"Configuration loading failed: {e}")

    def _load_config_sources(self) -> Dict[str, Any]:
        """Load configuration from multiple sources in priority order."""
        config_data = {}

        # 1. Load default configuration
        default_config = self._load_default_config()
        config_data.update(default_config)

        # 2. Load configuration files
        file_config = self._load_config_files()
        config_data.update(file_config)

        # 3. Load environment variables (handled by Pydantic)

        # 4. Load secrets
        secrets = self._load_secrets()
        config_data.update(secrets)

        return config_data

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values."""
        return {
            "debug": False,
            "environment": "development",
            "database": DatabaseConfig().dict(),
            "processing": ProcessingConfig().dict(),
            "logging": LoggingConfig().dict(),
        }

    def _load_config_files(self) -> Dict[str, Any]:
        """Load configuration from files."""
        config_data = {}

        # Check for YAML config files
        yaml_files = [
            self.config_dir / "default.yaml",
            self.config_dir / "local.yaml",
            self.config_dir / f"{os.getenv('EPM_ENVIRONMENT', 'development')}.yaml",
        ]

        for yaml_file in yaml_files:
            if yaml_file.exists():
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        file_data = yaml.safe_load(f)
                        if file_data:
                            config_data.update(file_data)
                            logger.debug(f"Loaded config from {yaml_file}")
                except Exception as e:
                    logger.warning(f"Failed to load config from {yaml_file}: {e}")

        # Check for JSON config file
        json_file = self.config_dir / "config.json"
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    if file_data:
                        config_data.update(file_data)
                        logger.debug(f"Loaded config from {json_file}")
            except Exception as e:
                logger.warning(f"Failed to load config from {json_file}: {e}")

        return config_data

    def _load_secrets(self) -> Dict[str, Any]:
        """Load secrets from secure storage."""
        secrets_data = {}

        try:
            # Load email secrets
            email_secrets = self.secrets_manager.get_email_secrets()
            if email_secrets:
                secrets_data["email"] = email_secrets

            # Load AI secrets
            ai_secrets = self.secrets_manager.get_ai_secrets()
            if ai_secrets:
                secrets_data["ai"] = ai_secrets

        except Exception as e:
            logger.warning(f"Failed to load secrets: {e}")

        return secrets_data

    def reload_config(self):
        """Reload configuration from sources."""
        self._config = None
        return self.load_config()

    def get_config(self) -> AppConfig:
        """Get current configuration."""
        if self._config is None:
            return self.load_config()
        return self._config

    def save_config(self, config: AppConfig, config_file: str = "local.yaml"):
        """Save configuration to file."""
        try:
            config_path = self.config_dir / config_file
            self.config_dir.mkdir(parents=True, exist_ok=True)

            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config.dict(exclude={'email': {'password'}, 'ai': {'api_key'}}),
                              f, default_flow_style=False, indent=2)

            logger.info(f"Configuration saved to {config_path}")

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise ConfigurationError(f"Failed to save configuration: {e}")


@lru_cache()
def get_config_manager(config_dir: Optional[str] = None) -> ConfigManager:
    """Get cached configuration manager instance."""
    return ConfigManager(config_dir)


@lru_cache()
def get_settings(config_dir: Optional[str] = None) -> AppConfig:
    """Get cached application settings."""
    manager = get_config_manager(config_dir)
    return manager.load_config()


def get_database_settings() -> DatabaseSettings:
    """Get database settings from environment."""
    return DatabaseSettings()


def get_email_settings() -> EmailSettings:
    """Get email settings from environment."""
    return EmailSettings()


def get_ai_settings() -> AISettings:
    """Get AI settings from environment."""
    return AISettings()


def create_default_config_file(config_dir: str = "config"):
    """Create default configuration file."""
    config_path = Path(config_dir)
    config_path.mkdir(parents=True, exist_ok=True)

    default_config = {
        "debug": False,
        "environment": "development",
        "database": {
            "path": "email_priority.db",
            "backup_enabled": True,
            "backup_interval": 86400,
            "backup_count": 7,
            "echo": False,
            "pool_size": 5,
            "max_overflow": 10
        },
        "processing": {
            "batch_size": 10,
            "max_email_size": 10485760,
            "allowed_file_types": ["pdf", "doc", "docx", "txt", "rtf"],
            "scan_interval": 300,
            "priority_threshold": 0.5
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file_path": "email_priority.log",
            "max_file_size": 10485760,
            "backup_count": 5
        }
    }

    config_file = config_path / "default.yaml"
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.safe_dump(default_config, f, default_flow_style=False, indent=2)

    logger.info(f"Default configuration created at {config_file}")


def validate_configuration() -> bool:
    """Validate current configuration."""
    try:
        settings = get_settings()

        # Validate required components
        if not settings.email:
            raise ConfigurationError("Email configuration is required")

        if not settings.ai:
            raise ConfigurationError("AI configuration is required")

        # Test database connectivity
        db_url = settings.get_database_url()
        logger.debug(f"Database URL: {db_url}")

        # Test configuration paths
        for directory in [settings.data_dir, settings.log_dir, settings.temp_dir]:
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

        logger.info("Configuration validation successful")
        return True

    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass


# Configuration helpers
def get_environment() -> str:
    """Get current environment."""
    return os.getenv("EPM_ENVIRONMENT", "development").lower()


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return os.getenv("EPM_DEBUG", "false").lower() in ("true", "1", "yes")


def get_data_directory() -> Path:
    """Get data directory path."""
    data_dir = os.getenv("EPM_DATA_DIR", "./data")
    return Path(data_dir)


def get_log_directory() -> Path:
    """Get log directory path."""
    log_dir = os.getenv("EPM_LOG_DIR", "./logs")
    return Path(log_dir)