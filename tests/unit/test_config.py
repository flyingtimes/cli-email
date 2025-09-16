"""
Unit tests for configuration management system.

Tests configuration loading, validation, and error handling.
"""

import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from email_priority_manager.config.models import (
    EmailConfig,
    DatabaseConfig,
    AIConfig,
    ProcessingConfig,
    LoggingConfig,
    AppConfig,
    ConfigurationError
)
from email_priority_manager.config.settings import (
    ConfigManager,
    get_settings,
    get_config_manager,
    validate_configuration,
    get_environment,
    is_debug_mode
)
from email_priority_manager.config.secrets import (
    SecretsManager,
    SecretsError,
    get_secrets_manager
)


class TestEmailConfig:
    """Test EmailConfig model."""

    def test_valid_email_config(self):
        """Test valid email configuration."""
        config = EmailConfig(
            server="smtp.test.com",
            port=587,
            username="test@example.com",
            password="test_password"
        )

        assert config.server == "smtp.test.com"
        assert config.port == 587
        assert config.username == "test@example.com"
        assert config.password.get_secret_value() == "test_password"
        assert config.use_ssl is True
        assert config.use_tls is True
        assert config.timeout == 30

    def test_invalid_port(self):
        """Test invalid port validation."""
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            EmailConfig(
                server="smtp.test.com",
                port=70000,  # Invalid port
                username="test@example.com",
                password="test_password"
            )

    def test_invalid_timeout(self):
        """Test invalid timeout validation."""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            EmailConfig(
                server="smtp.test.com",
                port=587,
                username="test@example.com",
                password="test_password",
                timeout=0  # Invalid timeout
            )


class TestDatabaseConfig:
    """Test DatabaseConfig model."""

    def test_valid_database_config(self):
        """Test valid database configuration."""
        config = DatabaseConfig(path="test.db")

        assert config.path == "test.db"
        assert config.backup_enabled is True
        assert config.backup_interval == 86400
        assert config.backup_count == 7

    def test_invalid_backup_interval(self):
        """Test invalid backup interval validation."""
        with pytest.raises(ValueError, match="Backup interval must be at least 3600 seconds"):
            DatabaseConfig(
                path="test.db",
                backup_interval=1800  # Too small
            )

    def test_invalid_backup_count(self):
        """Test invalid backup count validation."""
        with pytest.raises(ValueError, match="Backup count must be between 1 and 30"):
            DatabaseConfig(
                path="test.db",
                backup_count=0  # Invalid
            )


class TestAIConfig:
    """Test AIConfig model."""

    def test_valid_ai_config(self):
        """Test valid AI configuration."""
        config = AIConfig(
            api_key="test_api_key"
        )

        assert config.api_key.get_secret_value() == "test_api_key"
        assert config.model == "text-davinci-003"
        assert config.max_tokens == 1000
        assert config.temperature == 0.7

    def test_invalid_temperature(self):
        """Test invalid temperature validation."""
        with pytest.raises(ValueError, match="Temperature must be between 0.0 and 1.0"):
            AIConfig(
                api_key="test_api_key",
                temperature=1.5  # Invalid temperature
            )

    def test_invalid_max_tokens(self):
        """Test invalid max tokens validation."""
        with pytest.raises(ValueError, match="Max tokens must be between 1 and 4000"):
            AIConfig(
                api_key="test_api_key",
                max_tokens=0  # Invalid max tokens
            )


class TestProcessingConfig:
    """Test ProcessingConfig model."""

    def test_valid_processing_config(self):
        """Test valid processing configuration."""
        config = ProcessingConfig()

        assert config.batch_size == 10
        assert config.max_email_size == 10485760
        assert config.allowed_file_types == ["pdf", "doc", "docx", "txt", "rtf"]
        assert config.scan_interval == 300
        assert config.priority_threshold == 0.5

    def test_invalid_batch_size(self):
        """Test invalid batch size validation."""
        with pytest.raises(ValueError, match="Batch size must be between 1 and 100"):
            ProcessingConfig(
                batch_size=0  # Invalid batch size
            )

    def test_invalid_scan_interval(self):
        """Test invalid scan interval validation."""
        with pytest.raises(ValueError, match="Scan interval must be at least 60 seconds"):
            ProcessingConfig(
                scan_interval=30  # Too small
            )


class TestLoggingConfig:
    """Test LoggingConfig model."""

    def test_valid_logging_config(self):
        """Test valid logging configuration."""
        config = LoggingConfig()

        assert config.level == "INFO"
        assert "asctime" in config.format
        assert config.max_file_size == 10485760
        assert config.backup_count == 5

    def test_invalid_log_level(self):
        """Test invalid log level validation."""
        with pytest.raises(ValueError, match="Log level must be one of"):
            LoggingConfig(
                level="INVALID"  # Invalid log level
            )


class TestConfigManager:
    """Test ConfigManager class."""

    def test_config_manager_initialization(self, test_config_dir):
        """Test ConfigManager initialization."""
        manager = ConfigManager(str(test_config_dir))
        assert manager.config_dir == test_config_dir
        assert manager._config is None

    def test_load_default_config(self, test_config_dir):
        """Test loading default configuration."""
        manager = ConfigManager(str(test_config_dir))
        default_config = manager._load_default_config()

        assert default_config["debug"] is False
        assert default_config["environment"] == "development"
        assert "database" in default_config
        assert "processing" in default_config
        assert "logging" in default_config

    def test_load_config_files(self, test_config_dir):
        """Test loading configuration from files."""
        # Create test config file
        config_file = test_config_dir / "test.yaml"
        test_config_data = {
            "debug": True,
            "environment": "testing",
            "database": {"path": "test.db"}
        }

        with open(config_file, 'w') as f:
            yaml.safe_dump(test_config_data, f)

        manager = ConfigManager(str(test_config_dir))
        file_config = manager._load_config_files()

        assert file_config["debug"] is True
        assert file_config["environment"] == "testing"
        assert file_config["database"]["path"] == "test.db"

    @patch('email_priority_manager.config.settings.SecretsManager')
    def test_load_secrets(self, mock_secrets_class, test_config_dir):
        """Test loading secrets."""
        mock_secrets = Mock()
        mock_secrets.get_email_secrets.return_value = {
            "server": "smtp.test.com",
            "username": "test@example.com",
            "password": "test_password"
        }
        mock_secrets.get_ai_secrets.return_value = {
            "api_key": "test_api_key"
        }
        mock_secrets_class.return_value = mock_secrets

        manager = ConfigManager(str(test_config_dir))
        secrets = manager._load_secrets()

        assert "email" in secrets
        assert "ai" in secrets
        assert secrets["email"]["server"] == "smtp.test.com"
        assert secrets["ai"]["api_key"] == "test_api_key"

    def test_save_config(self, test_config_dir):
        """Test saving configuration to file."""
        manager = ConfigManager(str(test_config_dir))

        config = AppConfig(
            debug=True,
            environment="testing",
            email=EmailConfig(
                server="smtp.test.com",
                port=587,
                username="test@example.com",
                password="test_password"
            ),
            ai=AIConfig(api_key="test_api_key")
        )

        manager.save_config(config, "test.yaml")

        # Verify file was created
        config_file = test_config_dir / "test.yaml"
        assert config_file.exists()

        # Verify content
        with open(config_file, 'r') as f:
            saved_config = yaml.safe_load(f)

        assert saved_config["debug"] is True
        assert saved_config["environment"] == "testing"
        assert "password" not in saved_config["email"]  # Should be excluded
        assert "api_key" not in saved_config["ai"]  # Should be excluded


class TestSecretsManager:
    """Test SecretsManager class."""

    def test_secrets_manager_initialization(self, test_secrets_dir):
        """Test SecretsManager initialization."""
        with patch('email_priority_manager.config.secrets.os.chmod'):
            manager = SecretsManager(str(test_secrets_dir))
            assert manager.secrets_dir == test_secrets_dir
            assert manager._fernet is not None

    def test_store_and_retrieve_secret(self, test_secrets_dir):
        """Test storing and retrieving secrets."""
        with patch('email_priority_manager.config.secrets.os.chmod'):
            manager = SecretsManager(str(test_secrets_dir))

            # Store secret
            manager.store_secret("test_key", "test_value", "test_category")

            # Retrieve secret
            value = manager.get_secret("test_key", "test_category")
            assert value == "test_value"

    def test_delete_secret(self, test_secrets_dir):
        """Test deleting secrets."""
        with patch('email_priority_manager.config.secrets.os.chmod'):
            manager = SecretsManager(str(test_secrets_dir))

            # Store secret
            manager.store_secret("test_key", "test_value", "test_category")

            # Delete secret
            manager.delete_secret("test_key", "test_category")

            # Verify it's gone
            value = manager.get_secret("test_key", "test_category")
            assert value is None

    def test_list_secrets(self, test_secrets_dir):
        """Test listing secrets."""
        with patch('email_priority_manager.config.secrets.os.chmod'):
            manager = SecretsManager(str(test_secrets_dir))

            # Store multiple secrets
            manager.store_secret("key1", "value1", "category1")
            manager.store_secret("key2", "value2", "category1")
            manager.store_secret("key3", "value3", "category2")

            # List all secrets
            secrets = manager.list_secrets()
            assert "category1" in secrets
            assert "category2" in secrets
            assert "key1" in secrets["category1"]
            assert "key2" in secrets["category1"]
            assert "key3" in secrets["category2"]

            # List specific category
            category_secrets = manager.list_secrets("category1")
            assert "category1" in category_secrets
            assert "key1" in category_secrets["category1"]
            assert "key2" in category_secrets["category1"]

    def test_email_credentials_management(self, test_secrets_dir):
        """Test email credentials management."""
        with patch('email_priority_manager.config.secrets.os.chmod'):
            manager = SecretsManager(str(test_secrets_dir))

            # Store email credentials
            manager.store_email_credentials(
                "smtp.test.com", "test@example.com", "test_password", 587
            )

            # Retrieve email credentials
            credentials = manager.get_email_secrets()
            assert credentials is not None
            assert credentials["server"] == "smtp.test.com"
            assert credentials["username"] == "test@example.com"
            assert credentials["password"] == "test_password"
            assert credentials["port"] == 587

    def test_ai_credentials_management(self, test_secrets_dir):
        """Test AI credentials management."""
        with patch('email_priority_manager.config.secrets.os.chmod'):
            manager = SecretsManager(str(test_secrets_dir))

            # Store AI credentials
            manager.store_ai_credentials("test_api_key", "https://api.test.com")

            # Retrieve AI credentials
            credentials = manager.get_ai_secrets()
            assert credentials is not None
            assert credentials["api_key"] == "test_api_key"
            assert credentials["base_url"] == "https://api.test.com"


class TestConfigurationFunctions:
    """Test configuration utility functions."""

    def test_get_environment(self, mock_env_vars):
        """Test getting environment."""
        assert get_environment() == "testing"

    def test_is_debug_mode(self, mock_env_vars):
        """Test debug mode detection."""
        assert is_debug_mode() is True

    def test_validate_configuration_success(self, mock_env_vars, test_config_dir):
        """Test successful configuration validation."""
        # Create a minimal config file
        config_file = test_config_dir / "default.yaml"
        config_data = {
            "email": {
                "server": "smtp.test.com",
                "username": "test@example.com",
                "password": "test_password"
            },
            "ai": {
                "api_key": "test_api_key"
            }
        }

        with open(config_file, 'w') as f:
            yaml.safe_dump(config_data, f)

        with patch('email_priority_manager.config.settings.get_config_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.load_config.return_value = AppConfig(
                debug=True,
                environment="testing",
                email=EmailConfig(
                    server="smtp.test.com",
                    port=587,
                    username="test@example.com",
                    password="test_password"
                ),
                ai=AIConfig(api_key="test_api_key")
            )
            mock_get_manager.return_value = mock_manager

            assert validate_configuration() is True

    def test_validate_configuration_failure(self, mock_env_vars, test_config_dir):
        """Test failed configuration validation."""
        with patch('email_priority_manager.config.settings.get_config_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.load_config.side_effect = Exception("Configuration error")
            mock_get_manager.return_value = mock_manager

            assert validate_configuration() is False

    def test_get_config_manager_caching(self, test_config_dir):
        """Test ConfigManager caching."""
        manager1 = get_config_manager(str(test_config_dir))
        manager2 = get_config_manager(str(test_config_dir))

        assert manager1 is manager2  # Should be same instance due to caching

    def test_get_settings_caching(self, test_config_dir):
        """Test settings caching."""
        with patch('email_priority_manager.config.settings.get_config_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_config = AppConfig(
                debug=True,
                environment="testing",
                email=EmailConfig(
                    server="smtp.test.com",
                    port=587,
                    username="test@example.com",
                    password="test_password"
                ),
                ai=AIConfig(api_key="test_api_key")
            )
            mock_manager.load_config.return_value = mock_config
            mock_get_manager.return_value = mock_manager

            settings1 = get_settings(str(test_config_dir))
            settings2 = get_settings(str(test_config_dir))

            assert settings1 is settings2  # Should be same instance due to caching
            mock_manager.load_config.assert_called_once()  # Should only load once


class TestConfigurationErrorHandling:
    """Test configuration error handling."""

    def test_configuration_error_creation(self):
        """Test ConfigurationError creation."""
        error = ConfigurationError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_secrets_error_creation(self):
        """Test SecretsError creation."""
        error = SecretsError("Test secrets error")
        assert str(error) == "Test secrets error"
        assert isinstance(error, Exception)