"""
Database module for Email Priority Manager.

Handles data persistence and schema management for emails and settings.
"""

from .models import Email, Priority, Configuration
from .schema import DatabaseSchema
from .migrations import MigrationManager

__all__ = ["Email", "Priority", "Configuration", "DatabaseSchema", "MigrationManager"]