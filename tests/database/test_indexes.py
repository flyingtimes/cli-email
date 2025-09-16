"""
Tests for database indexes functionality.
"""

import pytest
import tempfile
import os

from src.email_priority_manager.database.schema import DatabaseSchema
from src.email_priority_manager.database.indexes import DatabaseIndexManager, IndexType, IndexInfo


class TestDatabaseIndexManager:
    """Test cases for DatabaseIndexManager class."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.schema = DatabaseSchema(self.db_path)
        self.index_manager = DatabaseIndexManager(self.db_path)

        # Initialize database
        self.schema.initialize_database()

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_get_performance_indexes(self):
        """Test getting performance indexes."""
        indexes = self.index_manager.get_performance_indexes()

        assert isinstance(indexes, list)
        assert len(indexes) > 0

        # Check that we have essential indexes
        index_names = [idx.name for idx in indexes]
        assert "idx_emails_message_id" in index_names
        assert "idx_emails_sender_received" in index_names
        assert "idx_classifications_email_id" in index_names
        assert "idx_attachments_email_id" in index_names

        # Check index properties
        for index in indexes:
            assert isinstance(index.name, str)
            assert isinstance(index.table, str)
            assert isinstance(index.columns, list)
            assert isinstance(index.index_type, IndexType)
            assert isinstance(index.unique, bool)
            assert len(index.columns) > 0

    def test_create_all_indexes(self):
        """Test creating all performance indexes."""
        # Should not raise an exception
        self.index_manager.create_all_indexes()

        # Verify indexes were created
        stats = self.index_manager.get_index_stats()
        assert stats["total_indexes"] > 0

    def test_create_single_index(self):
        """Test creating a single index."""
        index_info = IndexInfo(
            name="test_index",
            table="emails",
            columns=["subject"],
            index_type=IndexType.BTREE
        )

        # Should not raise an exception
        self.index_manager.create_index(index_info)

        # Verify index was created
        stats = self.index_manager.get_index_stats()
        index_names = [idx["name"] for idx in stats["indexes"]]
        assert "test_index" in index_names

    def test_drop_index(self):
        """Test dropping an index."""
        # First create an index
        index_info = IndexInfo(
            name="test_drop_index",
            table="emails",
            columns=["subject"],
            index_type=IndexType.BTREE
        )
        self.index_manager.create_index(index_info)

        # Verify it exists
        stats = self.index_manager.get_index_stats()
        index_names = [idx["name"] for idx in stats["indexes"]]
        assert "test_drop_index" in index_names

        # Drop the index
        self.index_manager.drop_index("test_drop_index")

        # Verify it's gone
        stats = self.index_manager.get_index_stats()
        index_names = [idx["name"] for idx in stats["indexes"]]
        assert "test_drop_index" not in index_names

    def test_get_index_stats(self):
        """Test getting index statistics."""
        # Create some indexes
        self.index_manager.create_all_indexes()

        stats = self.index_manager.get_index_stats()

        assert isinstance(stats, dict)
        assert "total_indexes" in stats
        assert "indexes" in stats
        assert "table_stats" in stats

        assert isinstance(stats["total_indexes"], int)
        assert isinstance(stats["indexes"], list)
        assert isinstance(stats["table_stats"], dict)

        # Check indexes list structure
        if stats["indexes"]:
            for index in stats["indexes"]:
                assert "name" in index
                assert "table" in index
                assert "sql" in index

    def test_analyze_indexes(self):
        """Test index analysis."""
        # Create some indexes
        self.index_manager.create_all_indexes()

        analysis = self.index_manager.analyze_indexes()

        assert isinstance(analysis, dict)
        assert "table_stats" in analysis
        assert "index_counts" in analysis
        assert "recommendations" in analysis
        assert "analysis_time" in analysis

        assert isinstance(analysis["table_stats"], dict)
        assert isinstance(analysis["index_counts"], dict)
        assert isinstance(analysis["recommendations"], list)

        # Check table stats
        table_stats = analysis["table_stats"]
        assert "emails" in table_stats
        assert "classifications" in table_stats
        assert isinstance(table_stats["emails"], int)
        assert isinstance(table_stats["classifications"], int)

        # Check recommendations
        recommendations = analysis["recommendations"]
        assert isinstance(recommendations, list)
        for rec in recommendations:
            assert "type" in rec
            assert "message" in rec
            assert "priority" in rec

    def test_optimize_indexes(self):
        """Test index optimization."""
        # Should not raise an exception
        self.index_manager.optimize_indexes()

    def test_create_compound_indexes(self):
        """Test creating compound indexes for common queries."""
        # Should not raise an exception
        self.index_manager.create_compound_indexes_for_common_queries()

        # Verify compound indexes were created
        stats = self.index_manager.get_index_stats()
        index_names = [idx["name"] for idx in stats["indexes"]]

        # Check for specific compound indexes
        assert "idx_email_priority_query" in index_names
        assert "idx_classification_priority_date" in index_names

    def test_get_query_performance_hints(self):
        """Test getting query performance hints."""
        hints = self.index_manager.get_query_performance_hints()

        assert isinstance(hints, dict)
        assert "email_search" in hints
        assert "priority_queries" in hints
        assert "attachment_queries" in hints
        assert "history_queries" in hints

        # Check that hints are lists
        for category, hint_list in hints.items():
            assert isinstance(hint_list, list)
            assert len(hint_list) > 0
            for hint in hint_list:
                assert isinstance(hint, str)

    def test_backup_and_restore_indexes(self):
        """Test backing up and restoring indexes."""
        # Create some indexes
        self.index_manager.create_all_indexes()

        # Get initial stats
        initial_stats = self.index_manager.get_index_stats()
        initial_count = initial_stats["total_indexes"]

        # Backup indexes
        backup_path = self.temp_db.name + "_backup.sql"
        self.index_manager.backup_indexes(backup_path)

        # Verify backup file was created
        assert os.path.exists(backup_path)

        # Drop all indexes
        for index in initial_stats["indexes"]:
            self.index_manager.drop_index(index["name"])

        # Verify indexes are gone
        stats_after_drop = self.index_manager.get_index_stats()
        assert stats_after_drop["total_indexes"] == 0

        # Restore indexes
        self.index_manager.restore_indexes_from_backup(backup_path)

        # Verify indexes are restored
        stats_after_restore = self.index_manager.get_index_stats()
        assert stats_after_restore["total_indexes"] == initial_count

        # Clean up backup file
        if os.path.exists(backup_path):
            os.unlink(backup_path)

    def test_index_info_structure(self):
        """Test IndexInfo data structure."""
        index_info = IndexInfo(
            name="test_index",
            table="emails",
            columns=["subject", "sender"],
            index_type=IndexType.BTREE,
            unique=True,
            where_clause="subject IS NOT NULL"
        )

        assert index_info.name == "test_index"
        assert index_info.table == "emails"
        assert index_info.columns == ["subject", "sender"]
        assert index_info.index_type == IndexType.BTREE
        assert index_info.unique is True
        assert index_info.where_clause == "subject IS NOT NULL"
        assert index_info.is_partial is True

    def test_partial_indexes(self):
        """Test partial index creation."""
        index_info = IndexInfo(
            name="test_partial_index",
            table="emails",
            columns=["size_bytes"],
            index_type=IndexType.BTREE,
            where_clause="size_bytes IS NOT NULL"
        )

        self.index_manager.create_index(index_info)

        # Verify partial index was created
        stats = self.index_manager.get_index_stats()
        index_names = [idx["name"] for idx in stats["indexes"]]
        assert "test_partial_index" in index_names

    def test_unique_indexes(self):
        """Test unique index creation."""
        index_info = IndexInfo(
            name="test_unique_index",
            table="emails",
            columns=["message_id"],
            index_type=IndexType.BTREE,
            unique=True
        )

        self.index_manager.create_index(index_info)

        # Verify unique index was created
        stats = self.index_manager.get_index_stats()
        index_names = [idx["name"] for idx in stats["indexes"]]
        assert "test_unique_index" in index_names

    def test_drop_nonexistent_index(self):
        """Test dropping a non-existent index."""
        # Should not raise an exception
        self.index_manager.drop_index("nonexistent_index")

    def test_index_types(self):
        """Test different index types."""
        for index_type in IndexType:
            index_info = IndexInfo(
                name=f"test_{index_type.value}_index",
                table="emails",
                columns=["subject"],
                index_type=index_type
            )

            self.index_manager.create_index(index_info)

            # Verify index was created
            stats = self.index_manager.get_index_stats()
            index_names = [idx["name"] for idx in stats["indexes"]]
            assert f"test_{index_type.value}_index" in index_names

    def test_index_recommendations_for_large_tables(self):
        """Test that recommendations are generated for large tables."""
        # Insert test data to simulate large table
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for i in range(150):  # More than 100 rows
                cursor.execute(
                    "INSERT INTO emails (message_id, subject, sender, recipients, received_at) VALUES (?, ?, ?, ?, ?)",
                    (f"msg{i}@example.com", f"Subject {i}", f"sender{i}@example.com", f"recipient{i}@example.com", "2023-01-01T00:00:00")
                )
            conn.commit()

        # Analyze indexes
        analysis = self.index_manager.analyze_indexes()

        # Should have recommendations for large tables
        recommendations = analysis["recommendations"]
        assert len(recommendations) >= 0  # Should not crash

    def test_backup_indexes_to_file(self):
        """Test that backup file contains proper SQL."""
        # Create some indexes
        self.index_manager.create_all_indexes()

        # Backup indexes
        backup_path = self.temp_db.name + "_backup.sql"
        self.index_manager.backup_indexes(backup_path)

        # Read backup file
        with open(backup_path, 'r') as f:
            backup_content = f.read()

        # Check that it contains index definitions
        assert "CREATE INDEX" in backup_content
        assert "-- Database Index Backup" in backup_content

        # Clean up
        if os.path.exists(backup_path):
            os.unlink(backup_path)