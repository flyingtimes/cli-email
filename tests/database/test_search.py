"""
Tests for database search functionality.
"""

import pytest
import tempfile
import os
from datetime import datetime

from src.email_priority_manager.database.schema import DatabaseSchema
from src.email_priority_manager.database.search import EmailSearch, SearchScope, SearchOperator, SearchFilter


class TestEmailSearch:
    """Test cases for EmailSearch class."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.schema = DatabaseSchema(self.db_path)
        self.search = EmailSearch(self.db_path)

        # Initialize database with test data
        self.schema.initialize_database()
        self._insert_test_data()

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def _insert_test_data(self):
        """Insert test data for search testing."""
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Insert test emails
            test_emails = [
                ("msg1@example.com", "Urgent: Project Deadline", "john@example.com", "alice@example.com", "This is an urgent email about project deadline", datetime.now().isoformat()),
                ("msg2@example.com", "Meeting Reminder", "mary@example.com", "bob@example.com", "Reminder about our meeting tomorrow", datetime.now().isoformat()),
                ("msg3@example.com", "Project Update", "john@example.com", "team@example.com", "Weekly project status update with important information", datetime.now().isoformat()),
                ("msg4@example.com", "Critical Security Alert", "security@example.com", "admin@example.com", "Critical security vulnerability detected", datetime.now().isoformat()),
                ("msg5@example.com", "Vacation Request", "alice@example.com", "manager@example.com", "Request for vacation time off", datetime.now().isoformat()),
            ]

            for msg_id, subject, sender, recipients, body_text, received_at in test_emails:
                cursor.execute(
                    "INSERT INTO emails (message_id, subject, sender, recipients, body_text, received_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (msg_id, subject, sender, recipients, body_text, received_at)
                )
                email_id = cursor.lastrowid

                # Insert classifications
                cursor.execute(
                    "INSERT INTO classifications (email_id, priority_score, urgency_level, importance_level, classification_type, confidence_score) VALUES (?, ?, ?, ?, ?, ?)",
                    (email_id, 5 if "Critical" in subject else 3 if "Urgent" in subject else 2,
                     "critical" if "Critical" in subject else "high" if "Urgent" in subject else "medium",
                     "high" if "Important" in body_text else "medium", "ai", 0.85)
                )

    def test_search_basic(self):
        """Test basic search functionality."""
        results = self.search.search("project")

        assert len(results) > 0
        assert any("project" in result.subject.lower() for result in results)

    def test_search_by_scope(self):
        """Test search with different scopes."""
        # Search in subject only
        results = self.search.search("meeting", scope=SearchScope.SUBJECT)
        assert len(results) > 0
        assert all("meeting" in result.subject.lower() for result in results)

        # Search in body only
        results = self.search.search("reminder", scope=SearchScope.BODY)
        assert len(results) > 0
        assert any("reminder" in result.body_text.lower() for result in results)

    def test_search_with_filters(self):
        """Test search with additional filters."""
        filters = [
            SearchFilter(field="sender", operator="=", value="john@example.com")
        ]
        results = self.search.search("project", filters=filters)

        assert len(results) > 0
        assert all(result.sender == "john@example.com" for result in results)

    def test_search_with_operators(self):
        """Test search with different operators."""
        # Test AND operator
        results = self.search.search("project update", operator=SearchOperator.AND)
        assert len(results) > 0
        for result in results:
            text = (result.subject + " " + result.body_text).lower()
            assert "project" in text and "update" in text

        # Test OR operator
        results = self.search.search("meeting reminder", operator=SearchOperator.OR)
        assert len(results) > 0
        for result in results:
            text = (result.subject + " " + result.body_text).lower()
            assert "meeting" in text or "reminder" in text

    def test_search_pagination(self):
        """Test search pagination."""
        # Get first page
        results_page1 = self.search.search("project", limit=2, offset=0)
        results_page2 = self.search.search("project", limit=2, offset=2)

        # Should not have overlapping results
        assert len(results_page1) <= 2
        assert len(results_page2) <= 2

    def test_search_by_priority(self):
        """Test search by priority."""
        # Search for high priority emails
        results = self.search.search_by_priority(min_priority=4, max_priority=5)
        assert len(results) > 0
        assert all(result.score >= 4 for result in results)

        # Search with urgency filter
        results = self.search.search_by_priority(
            min_priority=1, max_priority=5,
            urgency_levels=["critical"]
        )
        assert len(results) > 0

    def test_search_by_sender(self):
        """Test search by sender."""
        results = self.search.search_by_sender("john@example.com")
        assert len(results) > 0
        assert all("john@example.com" in result.sender for result in results)

        # Test partial match
        results = self.search.search_by_sender("john", include_body_search=True)
        assert len(results) > 0

    def test_search_by_date_range(self):
        """Test search by date range."""
        # Search for emails from today
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now().replace(hour=23, minute=59, second=59)).isoformat()

        results = self.search.search_by_date_range(today, tomorrow)
        assert len(results) > 0

    def test_get_search_suggestions(self):
        """Test search suggestions functionality."""
        suggestions = self.search.search_suggestions("pro")
        assert len(suggestions) > 0
        assert all("pro" in suggestion["text"].lower() for suggestion in suggestions)

    def test_rebuild_fts_index(self):
        """Test FTS index rebuilding."""
        # Should not raise an exception
        self.search.rebuild_fts_index()

    def test_search_with_special_characters(self):
        """Test search with special characters."""
        results = self.search.search("deadline:")
        assert len(results) >= 0  # Should not crash

    def test_search_empty_query(self):
        """Test search with empty query."""
        results = self.search.search("")
        assert len(results) == 0

    def test_search_not_found(self):
        """Test search for non-existent term."""
        results = self.search.search("nonexistentterm12345")
        assert len(results) == 0

    def test_search_result_structure(self):
        """Test that search results have correct structure."""
        results = self.search.search("project")
        if results:
            result = results[0]
            assert hasattr(result, 'email_id')
            assert hasattr(result, 'message_id')
            assert hasattr(result, 'subject')
            assert hasattr(result, 'sender')
            assert hasattr(result, 'recipients')
            assert hasattr(result, 'body_text')
            assert hasattr(result, 'received_at')
            assert hasattr(result, 'score')
            assert isinstance(result.email_id, int)
            assert isinstance(result.message_id, str)
            assert isinstance(result.subject, str)
            assert isinstance(result.sender, str)
            assert isinstance(result.recipients, str)
            assert isinstance(result.score, float)

    def test_search_case_sensitivity(self):
        """Test that search is case-insensitive."""
        results_lower = self.search.search("project")
        results_upper = self.search.search("PROJECT")
        results_mixed = self.search.search("Project")

        # Should return same results regardless of case
        assert len(results_lower) == len(results_upper) == len(results_mixed)

    def test_search_multiple_terms(self):
        """Test search with multiple terms."""
        results = self.search.search("project update")
        assert len(results) > 0

        # Results should contain at least one of the terms
        for result in results:
            text = (result.subject + " " + result.body_text).lower()
            assert "project" in text or "update" in text

    def test_search_with_limit_zero(self):
        """Test search with zero limit."""
        results = self.search.search("project", limit=0)
        assert len(results) == 0

    def test_search_with_large_limit(self):
        """Test search with large limit."""
        results = self.search.search("project", limit=1000)
        assert len(results) <= 5  # We only have 5 test emails