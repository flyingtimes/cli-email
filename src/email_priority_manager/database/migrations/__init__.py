"""
Database migrations for email priority manager.
Provides schema versioning and migration capabilities.
"""

from .migration_manager import MigrationManager
from .001_initial_schema import InitialSchemaMigration

__all__ = ['MigrationManager', 'InitialSchemaMigration']