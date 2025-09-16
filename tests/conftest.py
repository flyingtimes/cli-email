"""
Pytest configuration and fixtures for Email Priority Manager tests.

This module provides shared fixtures and configuration for all test modules.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock

from src.email_priority_manager.config.settings import Settings
from src.email_priority_manager.database.models import DatabaseManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_db_path(temp_dir):
    """Create a temporary database file path."""
    return temp_dir / "test.db"


@pytest.fixture
def test_config(temp_dir, temp_db_path):
    """Create test configuration."""
    config_data = {
        "email": {
            "server": "smtp.test.com",
            "port": 587,
            "username": "test@example.com",
            "password": "test_password",
            "use_ssl": True,
            "timeout": 30
        },
        "database": {
            "path": str(temp_db_path),
            "backup_enabled": False,
            "backup_interval": 86400
        },
        "ai": {
            "api_key": "test_api_key",
            "model": "test-model",
            "max_tokens": 1000,
            "temperature": 0.7
        },
        "debug": True,
        "log_level": "DEBUG"
    }

    # Create temporary config file
    config_file = temp_dir / "config.yaml"
    import yaml
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)

    return Settings(config_path=config_file)


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock(spec=Settings)
    settings.email.server = "smtp.test.com"
    settings.email.port = 587
    settings.email.username = "test@example.com"
    settings.email.password = "test_password"
    settings.database.path = ":memory:"
    settings.ai.api_key = "test_api_key"
    settings.ai.model = "test-model"
    settings.debug = True
    settings.log_level = "DEBUG"
    return settings


@pytest.fixture
def test_db_manager(test_config):
    """Create test database manager."""
    return DatabaseManager(test_config)


@pytest.fixture
def sample_email():
    """Sample email data for testing."""
    return {
        "id": "test_email_1",
        "sender": "sender@example.com",
        "subject": "Test Email Subject",
        "body": "This is a test email body for testing purposes.",
        "received_date": "2025-09-16T10:00:00Z",
        "priority": "medium"
    }


@pytest.fixture
def sample_emails():
    """Sample email data for testing."""
    return [
        {
            "id": "test_email_1",
            "sender": "urgent@example.com",
            "subject": "URGENT: Meeting Tomorrow",
            "body": "Important meeting scheduled for tomorrow at 2 PM.",
            "received_date": "2025-09-16T10:00:00Z",
            "priority": "high"
        },
        {
            "id": "test_email_2",
            "sender": "newsletter@example.com",
            "subject": "Weekly Newsletter",
            "body": "Here's your weekly newsletter with updates.",
            "received_date": "2025-09-16T11:00:00Z",
            "priority": "low"
        },
        {
            "id": "test_email_3",
            "sender": "colleague@example.com",
            "subject": "Project Update",
            "body": "Here's the latest update on our project progress.",
            "received_date": "2025-09-16T12:00:00Z",
            "priority": "medium"
        }
    ]


@pytest.fixture
def mock_ai_client():
    """Mock AI client for testing."""
    client = Mock()
    client.classify_email.return_value = "medium"
    client.analyze_content.return_value = {
        "priority": "medium",
        "confidence": 0.8,
        "reasoning": "Standard business email"
    }
    return client


@pytest.fixture
def mock_email_client():
    """Mock email client for testing."""
    client = Mock()
    client.connect.return_value = True
    client.get_emails.return_value = []
    client.send_email.return_value = True
    return client


# Test markers
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "ai: marks tests that require AI services"
    )
    config.addinivalue_line(
        "markers", "database: marks tests that require database"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add default markers."""
    for item in items:
        # Add unit marker by default if no other marker is present
        if not any(marker.name in ['slow', 'integration', 'ai', 'database'] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()