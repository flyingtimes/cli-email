"""
Database connection management and utilities.
"""

import sqlite3
import threading
from contextlib import contextmanager
from typing import Optional, Dict, Any, Union
from pathlib import Path
import time
import logging
from dataclasses import dataclass


@dataclass
class ConnectionConfig:
    """Database connection configuration."""
    db_path: str = "email_priority.db"
    timeout: float = 30.0
    check_same_thread: bool = False
    cached_statements: int = 100
    journal_mode: str = "WAL"
    synchronous: str = "NORMAL"
    temp_store: str = "MEMORY"
    mmap_size: int = 64 * 1024 * 1024  # 64MB
    page_size: int = 4096
    cache_size: int = -2000  # 2MB cache


class ConnectionPool:
    """Thread-safe database connection pool."""

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._connections: Dict[int, sqlite3.Connection] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection for the current thread."""
        thread_id = threading.get_ident()

        with self._lock:
            if thread_id not in self._connections:
                self._connections[thread_id] = self._create_connection()
                self._logger.debug(f"Created new connection for thread {thread_id}")

            return self._connections[thread_id]

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimized settings."""
        conn = sqlite3.connect(
            self.config.db_path,
            timeout=self.config.timeout,
            check_same_thread=self.config.check_same_thread,
            cached_statements=self.config.cached_statements
        )

        # Configure connection settings
        self._configure_connection(conn)
        return conn

    def _configure_connection(self, conn: sqlite3.Connection) -> None:
        """Configure connection settings for performance."""
        cursor = conn.cursor()

        # Set PRAGMA options for performance
        cursor.execute(f"PRAGMA journal_mode = {self.config.journal_mode}")
        cursor.execute(f"PRAGMA synchronous = {self.config.synchronous}")
        cursor.execute(f"PRAGMA temp_store = {self.config.temp_store}")
        cursor.execute(f"PRAGMA mmap_size = {self.config.mmap_size}")
        cursor.execute(f"PRAGMA page_size = {self.config.page_size}")
        cursor.execute(f"PRAGMA cache_size = {self.config.cache_size}")

        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")

        # Set busy timeout
        cursor.execute(f"PRAGMA busy_timeout = {int(self.config.timeout * 1000)}")

        conn.commit()

    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self._lock:
            for thread_id, conn in self._connections.items():
                try:
                    conn.close()
                    self._logger.debug(f"Closed connection for thread {thread_id}")
                except Exception as e:
                    self._logger.error(f"Error closing connection for thread {thread_id}: {e}")

            self._connections.clear()

    def cleanup(self) -> None:
        """Clean up closed connections."""
        with self._lock:
            dead_threads = []
            for thread_id, conn in self._connections.items():
                try:
                    # Test if connection is still alive
                    conn.execute("SELECT 1")
                except:
                    dead_threads.append(thread_id)

            for thread_id in dead_threads:
                try:
                    self._connections[thread_id].close()
                except:
                    pass
                del self._connections[thread_id]
                self._logger.debug(f"Cleaned up dead connection for thread {thread_id}")


class DatabaseManager:
    """High-level database connection manager."""

    def __init__(self, config: Optional[ConnectionConfig] = None):
        self.config = config or ConnectionConfig()
        self.pool = ConnectionPool(self.config)
        self._logger = logging.getLogger(__name__)

    def initialize_database(self) -> None:
        """Initialize the database file and directories."""
        db_path = Path(self.config.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Test connection
        with self.get_connection() as conn:
            conn.execute("SELECT 1")

        self._logger.info(f"Database initialized at {self.config.db_path}")

    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic cleanup."""
        conn = self.pool.get_connection()
        try:
            # Configure row factory for convenience
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            self._logger.error(f"Database error: {e}")
            raise
        finally:
            # Note: Connection is kept open for reuse by the pool
            pass

    @contextmanager
    def get_cursor(self):
        """Get a database cursor with automatic cleanup."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> sqlite3.Cursor:
        """Execute a query and return the cursor."""
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor

    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute an update query and return the number of affected rows."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.rowcount

    def execute_many(self, query: str, params_list: list) -> int:
        """Execute a query multiple times with different parameters."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount

    def execute_script(self, script: str) -> None:
        """Execute a SQL script."""
        with self.get_connection() as conn:
            conn.executescript(script)

    def backup_database(self, backup_path: str) -> None:
        """Create a backup of the database."""
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        with self.get_connection() as source_conn:
            backup_conn = sqlite3.connect(str(backup_path))
            source_conn.backup(backup_conn)
            backup_conn.close()

        self._logger.info(f"Database backed up to {backup_path}")

    def restore_database(self, backup_path: str) -> None:
        """Restore database from a backup."""
        backup_path = Path(backup_path)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Close existing connections
        self.pool.close_all()

        # Copy backup file
        import shutil
        shutil.copy2(str(backup_path), self.config.db_path)

        self._logger.info(f"Database restored from {backup_path}")

    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get database file info
            db_path = Path(self.config.db_path)
            file_size = db_path.stat().st_size if db_path.exists() else 0

            # Get SQLite version
            cursor.execute("SELECT sqlite_version()")
            sqlite_version = cursor.fetchone()[0]

            # Get page count and size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]

            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]

            # Get table counts
            tables = ["emails", "classifications", "attachments", "rules", "history", "tags", "email_tags"]
            table_counts = {}

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                table_counts[table] = cursor.fetchone()[0]

            # Get index info
            cursor.execute("""
                SELECT COUNT(*)
                FROM sqlite_master
                WHERE type='index'
                AND name NOT LIKE 'sqlite_%'
            """)
            index_count = cursor.fetchone()[0]

            return {
                "database_path": str(db_path),
                "file_size_bytes": file_size,
                "file_size_mb": file_size / (1024 * 1024),
                "sqlite_version": sqlite_version,
                "page_count": page_count,
                "page_size": page_size,
                "database_size_bytes": page_count * page_size,
                "table_counts": table_counts,
                "index_count": index_count,
                "total_emails": table_counts.get("emails", 0),
                "total_classifications": table_counts.get("classifications", 0),
                "total_attachments": table_counts.get("attachments", 0),
            }

    def optimize_database(self) -> None:
        """Optimize the database for better performance."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Analyze tables for query optimization
            cursor.execute("ANALYZE")

            # Vacuum to reclaim space
            cursor.execute("VACUUM")

            # Optimize indexes
            cursor.execute("PRAGMA optimize")

            conn.commit()

        self._logger.info("Database optimization completed")

    def check_integrity(self) -> bool:
        """Check database integrity."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            return result == "ok"

    def close(self) -> None:
        """Close all database connections."""
        self.pool.close_all()
        self._logger.info("Database manager closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(config: Optional[ConnectionConfig] = None) -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(config)
    return _db_manager


def initialize_database(config: Optional[ConnectionConfig] = None) -> DatabaseManager:
    """Initialize the database and return the manager."""
    manager = get_db_manager(config)
    manager.initialize_database()
    return manager


@contextmanager
def get_db_connection():
    """Context manager for getting database connections."""
    manager = get_db_manager()
    with manager.get_connection() as conn:
        yield conn


@contextmanager
def get_db_cursor():
    """Context manager for getting database cursors."""
    manager = get_db_manager()
    with manager.get_cursor() as cursor:
        yield cursor


def execute_query(query: str, params: Optional[tuple] = None) -> sqlite3.Cursor:
    """Execute a query using the global manager."""
    manager = get_db_manager()
    return manager.execute_query(query, params)


def execute_update(query: str, params: Optional[tuple] = None) -> int:
    """Execute an update using the global manager."""
    manager = get_db_manager()
    return manager.execute_update(query, params)


def close_database_connections():
    """Close all database connections."""
    global _db_manager
    if _db_manager is not None:
        _db_manager.close()
        _db_manager = None