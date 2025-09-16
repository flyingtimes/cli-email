"""
Tests for database schema functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.email_priority_manager.database.schema import DatabaseSchema


class TestDatabaseSchema:
    """Test cases for DatabaseSchema class."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.schema = DatabaseSchema(self.db_path)

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_database_schema_initialization(self):
        """Test database schema initialization."""
        # Ensure database doesn't exist initially
        assert not self.schema.database_exists()

        # Initialize database
        self.schema.initialize_database()

        # Check database was created
        assert self.schema.database_exists()

        # Check schema version was set
        version = self.schema.get_schema_version()
        assert version == 1

    def test_schema_sql_generation(self):
        """Test SQL generation for schema."""
        schema_sql = self.schema.get_schema_sql()

        # Check that essential SQL statements are included
        sql_text = ' '.join(schema_sql)

        # Check for emails table
        assert "CREATE TABLE IF NOT EXISTS emails" in sql_text
        assert "message_id TEXT UNIQUE NOT NULL" in sql_text
        assert "subject TEXT NOT NULL" in sql_text
        assert "sender TEXT NOT NULL" in sql_text

        # Check for classifications table
        assert "CREATE TABLE IF NOT EXISTS classifications" in sql_text
        assert "priority_score INTEGER NOT NULL" in sql_text
        assert "urgency_level TEXT NOT NULL" in sql_text

        # Check for foreign key constraints
        assert "FOREIGN KEY (email_id) REFERENCES emails" in sql_text

        # Check for attachments table
        assert "CREATE TABLE IF NOT EXISTS attachments" in sql_text

        # Check for rules table
        assert "CREATE TABLE IF NOT EXISTS rules" in sql_text

        # Check for history table
        assert "CREATE TABLE IF NOT EXISTS history" in sql_text

        # Check for tags and email_tags tables
        assert "CREATE TABLE IF NOT EXISTS tags" in sql_text
        assert "CREATE TABLE IF NOT EXISTS email_tags" in sql_text

    def test_indexes_sql_generation(self):
        """Test SQL generation for indexes."""
        indexes_sql = self.schema.get_indexes_sql()

        # Check that index SQL statements are generated
        assert len(indexes_sql) > 0

        # Check for essential indexes
        sql_text = ' '.join(indexes_sql)
        assert "CREATE INDEX IF NOT EXISTS idx_emails_message_id" in sql_text
        assert "CREATE INDEX IF NOT EXISTS idx_emails_sender" in sql_text
        assert "CREATE INDEX IF NOT EXISTS idx_emails_received_at" in sql_text
        assert "CREATE INDEX IF NOT EXISTS idx_classifications_email_id" in sql_text
        assert "CREATE INDEX IF NOT EXISTS idx_attachments_email_id" in sql_text

    def test_fts_sql_generation(self):
        """Test SQL generation for full-text search."""
        fts_sql = self.schema.get_fts_sql()

        # Check that FTS SQL statements are generated
        assert len(fts_sql) > 0

        # Check for FTS virtual table
        sql_text = ' '.join(fts_sql)
        assert "CREATE VIRTUAL TABLE IF NOT EXISTS email_fts USING fts5" in sql_text

        # Check for triggers
        assert "CREATE TRIGGER IF NOT EXISTS email_fts_insert" in sql_text
        assert "CREATE TRIGGER IF NOT EXISTS email_fts_delete" in sql_text
        assert "CREATE TRIGGER IF NOT EXISTS email_fts_update" in sql_text

    def test_database_table_creation(self):
        """Test that all tables are created successfully."""
        self.schema.initialize_database()

        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check that all tables exist
            tables = ["emails", "classifications", "attachments", "rules", "history", "tags", "email_tags", "schema_version"]
            for table in tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                result = cursor.fetchone()
                assert result is not None, f"Table {table} not found"

            # Check that FTS virtual table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_fts'")
            result = cursor.fetchone()
            assert result is not None, "FTS virtual table not found"

    def test_foreign_key_constraints(self):
        """Test that foreign key constraints are enforced."""
        self.schema.initialize_database()

        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")

            # Try to insert classification for non-existent email (should fail)
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO classifications (email_id, priority_score, urgency_level, importance_level, classification_type) VALUES (999, 1, 'low', 'low', 'test')"
                )

            # Try to insert attachment for non-existent email (should fail)
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO attachments (email_id, filename, file_path) VALUES (999, 'test.txt', '/path/to/test.txt')"
                )

    def test_unique_constraints(self):
        """Test that unique constraints are enforced."""
        self.schema.initialize_database()

        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Insert a test email
            cursor.execute(
                "INSERT INTO emails (message_id, subject, sender, recipients, received_at) VALUES (?, ?, ?, ?, ?)",
                ("test@example.com", "Test Subject", "sender@example.com", "recipient@example.com", "2023-01-01T00:00:00")
            )

            # Try to insert email with same message_id (should fail)
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO emails (message_id, subject, sender, recipients, received_at) VALUES (?, ?, ?, ?, ?)",
                    ("test@example.com", "Another Subject", "sender@example.com", "recipient@example.com", "2023-01-01T00:00:00")
                )

    def test_check_constraints(self):
        """Test that check constraints are enforced."""
        self.schema.initialize_database()

        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Insert a test email
            cursor.execute(
                "INSERT INTO emails (message_id, subject, sender, recipients, received_at) VALUES (?, ?, ?, ?, ?)",
                ("test@example.com", "Test Subject", "sender@example.com", "recipient@example.com", "2023-01-01T00:00:00")
            )
            email_id = cursor.lastrowid

            # Try to insert classification with invalid priority_score (should fail)
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO classifications (email_id, priority_score, urgency_level, importance_level, classification_type) VALUES (?, ?, ?, ?, ?)",
                    (email_id, 6, 'low', 'low', 'test')  # priority_score > 5
                )

            # Try to insert classification with invalid urgency_level (should fail)
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO classifications (email_id, priority_score, urgency_level, importance_level, classification_type) VALUES (?, ?, ?, ?, ?)",
                    (email_id, 3, 'invalid', 'low', 'test')  # invalid urgency_level
                )

    def test_cascade_delete(self):
        """Test that cascade delete works correctly."""
        self.schema.initialize_database()

        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Insert a test email
            cursor.execute(
                "INSERT INTO emails (message_id, subject, sender, recipients, received_at) VALUES (?, ?, ?, ?, ?)",
                ("test@example.com", "Test Subject", "sender@example.com", "recipient@example.com", "2023-01-01T00:00:00")
            )
            email_id = cursor.lastrowid

            # Insert classification
            cursor.execute(
                "INSERT INTO classifications (email_id, priority_score, urgency_level, importance_level, classification_type) VALUES (?, ?, ?, ?, ?)",
                (email_id, 3, 'medium', 'medium', 'test')
            )

            # Insert attachment
            cursor.execute(
                "INSERT INTO attachments (email_id, filename, file_path) VALUES (?, ?, ?)",
                (email_id, 'test.txt', '/path/to/test.txt')
            )

            # Verify related records exist
            cursor.execute("SELECT COUNT(*) FROM classifications WHERE email_id = ?", (email_id,))
            assert cursor.fetchone()[0] == 1

            cursor.execute("SELECT COUNT(*) FROM attachments WHERE email_id = ?", (email_id,))
            assert cursor.fetchone()[0] == 1

            # Delete the email
            cursor.execute("DELETE FROM emails WHERE id = ?", (email_id,))

            # Verify related records are deleted (cascade)
            cursor.execute("SELECT COUNT(*) FROM classifications WHERE email_id = ?", (email_id,))
            assert cursor.fetchone()[0] == 0

            cursor.execute("SELECT COUNT(*) FROM attachments WHERE email_id = ?", (email_id,))
            assert cursor.fetchone()[0] == 0

    def test_drop_database(self):
        """Test database dropping functionality."""
        # Initialize database
        self.schema.initialize_database()
        assert self.schema.database_exists()

        # Drop database
        self.schema.drop_database()
        assert not self.schema.database_exists()

    def test_schema_version_tracking(self):
        """Test schema version tracking."""
        # Check initial version (should be 0)
        version = self.schema.get_schema_version()
        assert version == 0

        # Initialize database
        self.schema.initialize_database()

        # Check version after initialization
        version = self.schema.get_schema_version()
        assert version == 1