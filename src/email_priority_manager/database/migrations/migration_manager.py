"""
Migration manager for database schema versioning.
Handles applying and rolling back migrations.
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from ..connection import get_db_manager, DatabaseOperationError

logger = logging.getLogger(__name__)


class Migration:
    """Base class for database migrations."""

    def __init__(self, version: int, name: str, description: str = ""):
        self.version = version
        self.name = name
        self.description = description
        self.applied_at: Optional[datetime] = None

    def up(self) -> List[str]:
        """
        Return SQL statements to apply the migration.

        Returns:
            List of SQL statements to execute
        """
        raise NotImplementedError("Subclasses must implement up() method")

    def down(self) -> List[str]:
        """
        Return SQL statements to rollback the migration.

        Returns:
            List of SQL statements to execute
        """
        raise NotImplementedError("Subclasses must implement down() method")

    def check_prerequisites(self, db_manager) -> bool:
        """
        Check if prerequisites for this migration are met.

        Args:
            db_manager: Database connection manager

        Returns:
            True if prerequisites are met
        """
        return True

    def post_apply(self, db_manager) -> None:
        """
        Perform post-migration operations.

        Args:
            db_manager: Database connection manager
        """
        pass


class MigrationManager:
    """Manages database migrations and versioning."""

    def __init__(self, db_manager=None):
        """
        Initialize the migration manager.

        Args:
            db_manager: Database connection manager instance
        """
        self.db_manager = db_manager or get_db_manager()
        self.migrations: Dict[int, Migration] = {}
        self._load_migrations()

    def _load_migrations(self):
        """Load all available migrations."""
        # Import migrations here to avoid circular imports
        from .001_initial_schema import InitialSchemaMigration

        # Register migrations
        self.register_migration(InitialSchemaMigration())

        logger.info(f"Loaded {len(self.migrations)} migrations")

    def register_migration(self, migration: Migration):
        """
        Register a migration.

        Args:
            migration: Migration instance to register
        """
        if migration.version in self.migrations:
            raise MigrationError(f"Migration version {migration.version} already registered")

        self.migrations[migration.version] = migration
        logger.debug(f"Registered migration {migration.version}: {migration.name}")

    def get_current_version(self) -> Optional[int]:
        """
        Get the current database schema version.

        Returns:
            Current version number or None if no migrations applied
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT MAX(version) FROM schema_version")
                result = cursor.fetchone()
                return result[0] if result and result[0] is not None else None
        except sqlite3.OperationalError:
            # Schema version table doesn't exist
            return None

    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """
        Get list of applied migrations.

        Returns:
            List of migration information dictionaries
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT version, applied_at, description
                    FROM schema_version
                    ORDER BY version
                """)
                rows = cursor.fetchall()

                return [
                    {
                        'version': row[0],
                        'applied_at': row[1],
                        'description': row[2]
                    }
                    for row in rows
                ]
        except sqlite3.OperationalError:
            return []

    def get_pending_migrations(self) -> List[Migration]:
        """
        Get list of pending migrations.

        Returns:
            List of migrations that haven't been applied yet
        """
        current_version = self.get_current_version()

        if current_version is None:
            return list(self.migrations.values())

        pending = []
        for version, migration in sorted(self.migrations.items()):
            if version > current_version:
                pending.append(migration)

        return pending

    def migrate_to_version(self, target_version: int) -> None:
        """
        Migrate database to specific version.

        Args:
            target_version: Target version to migrate to
        """
        current_version = self.get_current_version()

        if current_version == target_version:
            logger.info(f"Database already at version {target_version}")
            return

        if current_version is None and target_version > 0:
            # Start from version 0
            current_version = 0

        if target_version > current_version:
            self._migrate_up(current_version, target_version)
        else:
            self._migrate_down(current_version, target_version)

    def migrate_up(self, steps: int = 1) -> None:
        """
        Apply pending migrations.

        Args:
            steps: Number of migrations to apply (default: 1)
        """
        pending = self.get_pending_migrations()

        if not pending:
            logger.info("No pending migrations")
            return

        migrations_to_apply = pending[:steps]
        current_version = self.get_current_version() or 0

        for migration in migrations_to_apply:
            self._apply_migration(migration)
            current_version = migration.version

    def migrate_down(self, steps: int = 1) -> None:
        """
        Rollback migrations.

        Args:
            steps: Number of migrations to rollback (default: 1)
        """
        applied = self.get_applied_migrations()

        if not applied:
            logger.info("No migrations to rollback")
            return

        migrations_to_rollback = applied[-steps:]
        target_version = applied[-steps-1]['version'] if len(applied) > steps else 0

        self.migrate_to_version(target_version)

    def _migrate_up(self, from_version: int, to_version: int) -> None:
        """
        Migrate up from one version to another.

        Args:
            from_version: Starting version
            to_version: Target version
        """
        for version in range(from_version + 1, to_version + 1):
            if version in self.migrations:
                migration = self.migrations[version]
                self._apply_migration(migration)
            else:
                raise MigrationError(f"Migration {version} not found")

    def _migrate_down(self, from_version: int, to_version: int) -> None:
        """
        Migrate down from one version to another.

        Args:
            from_version: Starting version
            to_version: Target version
        """
        for version in range(from_version, to_version, -1):
            if version in self.migrations:
                migration = self.migrations[version]
                self._rollback_migration(migration)
            else:
                raise MigrationError(f"Migration {version} not found")

    def _apply_migration(self, migration: Migration) -> None:
        """
        Apply a single migration.

        Args:
            migration: Migration to apply
        """
        logger.info(f"Applying migration {migration.version}: {migration.name}")

        try:
            # Check prerequisites
            if not migration.check_prerequisites(self.db_manager):
                raise MigrationError(f"Prerequisites not met for migration {migration.version}")

            # Get SQL statements
            statements = migration.up()

            # Execute statements in a transaction
            with self.db_manager.transaction() as conn:
                for statement in statements:
                    conn.execute(statement)

                # Record migration
                conn.execute(
                    "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                    (migration.version, migration.description)
                )

                migration.applied_at = datetime.now()

            # Post-apply operations
            migration.post_apply(self.db_manager)

            logger.info(f"Successfully applied migration {migration.version}")

        except Exception as e:
            logger.error(f"Failed to apply migration {migration.version}: {e}")
            raise MigrationError(f"Migration {migration.version} failed: {e}")

    def _rollback_migration(self, migration: Migration) -> None:
        """
        Rollback a single migration.

        Args:
            migration: Migration to rollback
        """
        logger.info(f"Rolling back migration {migration.version}: {migration.name}")

        try:
            # Get SQL statements
            statements = migration.down()

            # Execute statements in a transaction
            with self.db_manager.transaction() as conn:
                # Execute rollback statements
                for statement in statements:
                    conn.execute(statement)

                # Remove migration record
                conn.execute(
                    "DELETE FROM schema_version WHERE version = ?",
                    (migration.version,)
                )

                migration.applied_at = None

            logger.info(f"Successfully rolled back migration {migration.version}")

        except Exception as e:
            logger.error(f"Failed to rollback migration {migration.version}: {e}")
            raise MigrationError(f"Rollback {migration.version} failed: {e}")

    def create_database(self) -> None:
        """
        Create the database and apply all migrations.
        """
        logger.info("Creating database and applying migrations")

        # Apply all migrations
        if self.migrations:
            max_version = max(self.migrations.keys())
            self.migrate_to_version(max_version)

        logger.info("Database created successfully")

    def reset_database(self) -> None:
        """
        Reset the database by dropping all tables and recreating.
        """
        logger.warning("Resetting database - all data will be lost")

        try:
            # Get all migrations in reverse order
            applied = self.get_applied_migrations()
            if applied:
                current_version = applied[-1]['version']
                self.migrate_to_version(0)

            # Recreate from scratch
            self.create_database()

            logger.info("Database reset successfully")

        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            raise MigrationError(f"Database reset failed: {e}")

    def get_migration_status(self) -> Dict[str, Any]:
        """
        Get migration status information.

        Returns:
            Dictionary with migration status
        """
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        current_version = self.get_current_version()

        return {
            'current_version': current_version,
            'total_migrations': len(self.migrations),
            'applied_count': len(applied),
            'pending_count': len(pending),
            'applied_migrations': applied,
            'pending_migrations': [m.name for m in pending],
            'database_path': self.db_manager.db_path
        }

    def validate_migrations(self) -> bool:
        """
        Validate that all migrations are properly defined.

        Returns:
            True if all migrations are valid
        """
        for version, migration in sorted(self.migrations.items()):
            try:
                # Test that up() returns valid SQL
                up_statements = migration.up()
                if not up_statements:
                    logger.warning(f"Migration {version} has no up() statements")

                # Test that down() returns valid SQL
                down_statements = migration.down()
                if not down_statements:
                    logger.warning(f"Migration {version} has no down() statements")

                # Check prerequisites
                if not migration.check_prerequisites(self.db_manager):
                    logger.warning(f"Migration {version} prerequisites not met")

            except Exception as e:
                logger.error(f"Migration {version} validation failed: {e}")
                return False

        return True


class MigrationError(Exception):
    """Raised when migration operations fail."""
    pass


# Convenience functions
def get_migration_manager(db_manager=None) -> MigrationManager:
    """
    Get the migration manager instance.

    Args:
        db_manager: Optional database connection manager

    Returns:
        MigrationManager instance
    """
    return MigrationManager(db_manager)


def migrate(steps: int = 1) -> None:
    """
    Apply pending migrations.

    Args:
        steps: Number of migrations to apply
    """
    manager = get_migration_manager()
    manager.migrate_up(steps)


def rollback(steps: int = 1) -> None:
    """
    Rollback migrations.

    Args:
        steps: Number of migrations to rollback
    """
    manager = get_migration_manager()
    manager.migrate_down(steps)


def create_database() -> None:
    """Create database and apply all migrations."""
    manager = get_migration_manager()
    manager.create_database()


def reset_database() -> None:
    """Reset database by dropping and recreating."""
    manager = get_migration_manager()
    manager.reset_database()


def get_migration_status() -> Dict[str, Any]:
    """
    Get migration status information.

    Returns:
        Dictionary with migration status
    """
    manager = get_migration_manager()
    return manager.get_migration_status()