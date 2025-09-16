"""
Pytest configuration and fixtures for Email Priority Manager tests.

Provides common fixtures, configuration, and setup for all test modules.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(scope="session")
def test_dir() -> Generator[Path, None, None]:
    """Create temporary directory for tests."""
    temp_dir = Path(tempfile.mkdtemp(prefix="epm_test_"))

    yield temp_dir

    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def test_config_dir(test_dir: Path) -> Path:
    """Create test configuration directory."""
    config_dir = test_dir / "config"
    config_dir.mkdir(exist_ok=True)
    return config_dir


@pytest.fixture(scope="session")
def test_secrets_dir(test_dir: Path) -> Path:
    """Create test secrets directory."""
    secrets_dir = test_dir / "secrets"
    secrets_dir.mkdir(exist_ok=True)
    return secrets_dir


@pytest.fixture(scope="session")
def test_data_dir(test_dir: Path) -> Path:
    """Create test data directory."""
    data_dir = test_dir / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture
def mock_env_vars() -> Generator[Dict[str, str], None, None]:
    """Mock environment variables for testing."""
    original_env = os.environ.copy()

    test_env = {
        "EPM_DEBUG": "true",
        "EPM_ENVIRONMENT": "testing",
        "EPM_EMAIL_SERVER": "smtp.test.com",
        "EPM_EMAIL_PORT": "587",
        "EPM_EMAIL_USERNAME": "test@example.com",
        "EPM_EMAIL_PASSWORD": "test_password",
        "EPM_AI_API_KEY": "test_api_key",
        "EPM_SECRETS_PASSPHRASE": "test_passphrase",
        "EPM_DATA_DIR": "./test_data",
        "EPM_LOG_DIR": "./test_logs",
        "EPM_TEMP_DIR": "./test_temp",
    }

    # Set test environment variables
    for key, value in test_env.items():
        os.environ[key] = value

    yield test_env

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_email_config() -> Dict[str, Any]:
    """Sample email configuration for testing."""
    return {
        "server": "smtp.test.com",
        "port": 587,
        "username": "test@example.com",
        "password": "test_password",
        "use_ssl": True,
        "use_tls": True,
        "timeout": 30,
        "max_retries": 3,
    }


@pytest.fixture
def sample_ai_config() -> Dict[str, Any]:
    """Sample AI configuration for testing."""
    return {
        "api_key": "test_api_key",
        "model": "text-davinci-003",
        "max_tokens": 1000,
        "temperature": 0.7,
        "timeout": 30,
        "base_url": None,
    }


@pytest.fixture
def sample_database_config() -> Dict[str, Any]:
    """Sample database configuration for testing."""
    return {
        "path": "test.db",
        "backup_enabled": True,
        "backup_interval": 86400,
        "backup_count": 7,
        "echo": False,
        "pool_size": 5,
        "max_overflow": 10,
    }


@pytest.fixture
def sample_processing_config() -> Dict[str, Any]:
    """Sample processing configuration for testing."""
    return {
        "batch_size": 10,
        "max_email_size": 10485760,
        "allowed_file_types": ["pdf", "doc", "docx", "txt", "rtf"],
        "scan_interval": 300,
        "priority_threshold": 0.5,
    }


@pytest.fixture
def sample_logging_config() -> Dict[str, Any]:
    """Sample logging configuration for testing."""
    return {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file_path": "test.log",
        "max_file_size": 10485760,
        "backup_count": 5,
    }