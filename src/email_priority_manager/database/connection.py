"""
Database connection management for email priority manager.
Provides connection pooling, error handling, and transaction management.
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    """Manages SQLite database connections with thread safety and error handling."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database connection manager.

        Args:
            db_path: Path to the SQLite database file. If None, uses default location.
        """
        self.db_path = db_path or self._get_default_db_path()
        self.local = threading.local()
        self.lock = threading.Lock()

        # Ensure database directory exists
        self._ensure_db_directory()

        logger.info(f"Database connection manager initialized with path: {self.db_path}")

    def _get_default_db_path(self) -> str:
        """Get the default database file path."""
        # Use user's home directory for database storage
        home_dir = Path.home()
        db_dir = home_dir / '.email-priority-manager'
        db_dir.mkdir(parents=True, exist_ok=True)
        return str(db_dir / 'emails.db')

    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection for the current thread.

        Returns:
            SQLite connection object
        """
        if not hasattr(self.local, 'connection'):
            self.local.connection = self._create_connection()
        return self.local.connection

    def _create_connection(self) -> sqlite3.Connection:
        """
        Create a new database connection with proper configuration.

        Returns:
            Configured SQLite connection
        """
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,  # 30 second timeout
                check_same_thread=False,  # We handle thread safety ourselves
                isolation_level='DEFERRED',
                cached_statements=100  # Cache prepared statements
            )

            # Configure connection settings
            conn.execute('PRAGMA foreign_keys = ON')  # Enable foreign key constraints
            conn.execute('PRAGMA journal_mode = WAL')  # Write-Ahead Logging for better concurrency
            conn.execute('PRAGMA synchronous = NORMAL')  # Balance between safety and performance
            conn.execute('PRAGMA cache_size = -10000')  # 10MB cache
            conn.execute('PRAGMA temp_store = MEMORY')  # Use memory for temporary storage
            conn.execute('PRAGMA mmap_size = 268435456')  # 256MB memory mapping

            # Register custom functions
            self._register_custom_functions(conn)

            logger.debug(f"Created new database connection to {self.db_path}")
            return conn

        except sqlite3.Error as e:
            logger.error(f"Failed to create database connection: {e}")
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")

    def _register_custom_functions(self, conn: sqlite3.Connection):
        """Register custom SQLite functions."""
        # Example: Register a function for case-insensitive string comparison
        def case_insensitive_compare(a: str, b: str) -> bool:
            return a.lower() == b.lower()

        conn.create_function('CASE_INSENSITIVE_COMPARE', 2, case_insensitive_compare)

    @contextmanager
    def get_cursor(self):
        """
        Context manager for getting a database cursor.

        Yields:
            SQLite cursor object
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.

        Yields:
            SQLite connection object
        """
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
            logger.debug("Transaction committed successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise DatabaseTransactionError(f"Transaction failed: {e}")

    def close_connection(self):
        """Close the connection for the current thread."""
        if hasattr(self.local, 'connection'):
            try:
                self.local.connection.close()
                delattr(self.local, 'connection')
                logger.debug("Database connection closed")
            except sqlite3.Error as e:
                logger.error(f"Error closing database connection: {e}")

    def close_all_connections(self):
        """Close all database connections across all threads."""
        # Note: This is a best-effort approach since we can't access other threads' local storage
        # In practice, connections will be cleaned up when threads terminate
        logger.info("Request to close all connections (best-effort)")

    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute a query and return the cursor.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            Cursor with results
        """
        with self.get_cursor() as cursor:
            try:
                cursor.execute(query, params)
                return cursor
            except sqlite3.Error as e:
                logger.error(f"Query execution failed: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Parameters: {params}")
                raise DatabaseQueryError(f"Query failed: {e}")

    def execute_script(self, script: str) -> None:
        """
        Execute a multi-statement SQL script.

        Args:
            script: SQL script to execute
        """
        conn = self.get_connection()
        try:
            conn.executescript(script)
            conn.commit()
            logger.debug("SQL script executed successfully")
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Script execution failed: {e}")
            raise DatabaseQueryError(f"Script execution failed: {e}")

    def get_table_info(self, table_name: str) -> list:
        """
        Get information about a table's schema.

        Args:
            table_name: Name of the table

        Returns:
            List of column information tuples
        """
        query = f"PRAGMA table_info({table_name})"
        cursor = self.execute_query(query)
        return cursor.fetchall()

    def get_table_names(self) -> list:
        """
        Get list of all table names in the database.

        Returns:
            List of table names
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        cursor = self.execute_query(query)
        return [row[0] for row in cursor.fetchall()]

    def get_index_info(self) -> list:
        """
        Get information about all indexes in the database.

        Returns:
            List of index information tuples
        """
        query = "SELECT * FROM sqlite_master WHERE type='index' ORDER BY name"
        cursor = self.execute_query(query)
        return cursor.fetchall()

    def database_exists(self) -> bool:
        """
        Check if the database file exists.

        Returns:
            True if database file exists
        """
        return Path(self.db_path).exists()

    def get_database_size(self) -> int:
        """
        Get the size of the database file in bytes.

        Returns:
            Database file size in bytes
        """
        try:
            return Path(self.db_path).stat().st_size
        except FileNotFoundError:
            return 0

    def vacuum(self):
        """Rebuild the database to reclaim space and defragment."""
        try:
            with self.transaction() as conn:
                conn.execute('VACUUM')
            logger.info("Database vacuum completed")
        except sqlite3.Error as e:
            logger.error(f"Database vacuum failed: {e}")
            raise DatabaseOperationError(f"Vacuum failed: {e}")

    def backup(self, backup_path: str) -> None:
        """
        Create a backup of the database.

        Args:
            backup_path: Path for the backup file
        """
        try:
            # Ensure backup directory exists
            backup_dir = Path(backup_path).parent
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Use SQLite backup API
            with self.get_connection() as source_conn:
                backup_conn = sqlite3.connect(backup_path)
                source_conn.backup(backup_conn)
                backup_conn.close()

            logger.info(f"Database backup created at {backup_path}")
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            raise DatabaseOperationError(f"Backup failed: {e}")

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get database connection statistics.

        Returns:
            Dictionary with connection statistics
        """
        return {
            'database_path': self.db_path,
            'database_exists': self.database_exists(),
            'database_size_bytes': self.get_database_size(),
            'thread_local_connections': hasattr(self.local, 'connection'),
            'table_count': len(self.get_table_names()),
            'index_count': len(self.get_index_info())
        }


# Custom exceptions
class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""
    pass


class DatabaseTransactionError(Exception):
    """Raised when database transaction fails."""
    pass


class DatabaseQueryError(Exception):
    """Raised when database query fails."""
    pass


class DatabaseOperationError(Exception):
    """Raised when database operation fails."""
    pass


# Global connection manager instance
_db_manager: Optional[DatabaseConnectionManager] = None


def get_db_manager(db_path: Optional[str] = None) -> DatabaseConnectionManager:
    """
    Get the global database connection manager instance.

    Args:
        db_path: Optional database path override

    Returns:
        DatabaseConnectionManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseConnectionManager(db_path)
    return _db_manager


def close_global_connection():
    """Close the global database connection."""
    global _db_manager
    if _db_manager is not None:
        _db_manager.close_connection()
        _db_manager = None


def set_database_path(db_path: str):
    """
    Set the database path and reinitialize the connection manager.

    Args:
        db_path: New database path
    """
    global _db_manager
    if _db_manager is not None:
        _db_manager.close_connection()
    _db_manager = DatabaseConnectionManager(db_path)


# Convenience functions
def get_connection() -> sqlite3.Connection:
    """Get a database connection using the global manager."""
    return get_db_manager().get_connection()


@contextmanager
def get_cursor():
    """Context manager for getting a database cursor."""
    with get_db_manager().get_cursor() as cursor:
        yield cursor


@contextmanager
def transaction():
    """Context manager for database transactions."""
    with get_db_manager().transaction() as conn:
        yield conn


def execute_query(query: str, params: tuple = ()) -> sqlite3.Cursor:
    """Execute a query using the global manager."""
    return get_db_manager().execute_query(query, params)


def execute_script(script: str) -> None:
    """Execute a script using the global manager."""
    get_db_manager().execute_script(script)