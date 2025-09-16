"""
Tests for database query functionality.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta

from src.email_priority_manager.database.schema import DatabaseSchema
from src.email_priority_manager.database.queries import (
    EmailQueries, QueryOptions, QueryFilter, PriorityLevel, UrgencyLevel
)


class TestEmailQueries:
    """Test cases for EmailQueries class."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.schema = DatabaseSchema(self.db_path)
        self.queries = EmailQueries(self.db_path)

        # Initialize database with test data
        self.schema.initialize_database()
        self._insert_test_data()

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def _insert_test_data(self):
        """Insert test data for query testing."""
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Insert test emails with varying priorities
            test_emails = [
                ("msg1@example.com", "Critical: System Down", "admin@example.com", "team@example.com", "System is down, urgent action needed", datetime.now().isoformat()),
                ("msg2@example.com", "Project Update", "manager@example.com", "team@example.com", "Weekly project status update", datetime.now().isoformat()),
                ("msg3@example.com", "Budget Approval", "finance@example.com", "ceo@example.com", "Budget approval for Q4", datetime.now().isoformat()),
                ("msg4@example.com", "Team Meeting", "hr@example.com", "all@example.com", "Monthly team meeting", datetime.now().isoformat()),
                ("msg5@example.com", "Security Alert", "security@example.com", "admin@example.com", "Potential security breach detected", datetime.now().isoformat()),
            ]

            priorities = [5, 3, 4, 2, 5]  # Critical, Normal, High, Low, Critical
            urgencies = ["critical", "medium", "high", "low", "critical"]

            for i, (msg_id, subject, sender, recipients, body_text, received_at) in enumerate(test_emails):
                cursor.execute(
                    "INSERT INTO emails (message_id, subject, sender, recipients, body_text, received_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (msg_id, subject, sender, recipients, body_text, received_at)
                )
                email_id = cursor.lastrowid

                # Insert classifications
                cursor.execute(
                    "INSERT INTO classifications (email_id, priority_score, urgency_level, importance_level, classification_type, confidence_score) VALUES (?, ?, ?, ?, ?, ?)",
                    (email_id, priorities[i], urgencies[i], urgencies[i], "ai", 0.85)
                )

                # Add some attachments
                if i in [0, 2, 4]:  # Some emails have attachments
                    cursor.execute(
                        "INSERT INTO attachments (email_id, filename, file_path, size_bytes) VALUES (?, ?, ?, ?)",
                        (email_id, f"attachment_{i}.pdf", f"/path/to/attachment_{i}.pdf", 1024 * (i + 1))
                    )

            # Insert tags
            cursor.execute("INSERT INTO tags (name, description) VALUES (?, ?)", ("urgent", "Urgent emails"))
            cursor.execute("INSERT INTO tags (name, description) VALUES (?, ?)", ("project", "Project related"))
            cursor.execute("INSERT INTO tags (name, description) VALUES (?, ?)", ("security", "Security related"))

            tag_id_urgent = cursor.lastrowid - 2
            tag_id_project = cursor.lastrowid - 1
            tag_id_security = cursor.lastrowid

            # Assign tags to emails
            cursor.execute("INSERT INTO email_tags (email_id, tag_id) VALUES (?, ?)", (1, tag_id_urgent))
            cursor.execute("INSERT INTO email_tags (email_id, tag_id) VALUES (?, ?)", (2, tag_id_project))
            cursor.execute("INSERT INTO email_tags (email_id, tag_id) VALUES (?, ?)", (5, tag_id_security))

    def test_get_emails_by_priority(self):
        """Test getting emails by priority range."""
        # Get high priority emails (4-5)
        emails, count = self.queries.get_emails_by_priority(
            min_priority=4, max_priority=5,
            options=QueryOptions(limit=10, include_count=True)
        )

        assert len(emails) > 0
        assert all(email.priority_score >= 4 for email in emails)
        assert count is not None
        assert count >= len(emails)

    def test_get_emails_by_urgency(self):
        """Test getting emails by urgency levels."""
        # Get critical and high urgency emails
        emails, count = self.queries.get_emails_by_urgency(
            urgency_levels=["critical", "high"],
            options=QueryOptions(limit=10, include_count=True)
        )

        assert len(emails) > 0
        assert all(email.urgency_level in ["critical", "high"] for email in emails)
        assert count is not None

    def test_get_email_by_id(self):
        """Test getting email by ID."""
        # Get first email
        emails, _ = self.queries.get_emails_by_priority(
            min_priority=1, max_priority=5,
            options=QueryOptions(limit=1)
        )

        if emails:
            email_id = emails[0].id
            detail = self.queries.get_email_by_id(email_id)

            assert detail is not None
            assert detail.id == email_id
            assert detail.subject is not None
            assert detail.sender is not None
            assert detail.recipients is not None

    def test_get_email_by_id_not_found(self):
        """Test getting non-existent email by ID."""
        detail = self.queries.get_email_by_id(99999)
        assert detail is None

    def test_get_emails_by_sender(self):
        """Test getting emails by sender."""
        emails, count = self.queries.get_emails_by_sender(
            "admin@example.com",
            options=QueryOptions(limit=10, include_count=True)
        )

        assert len(emails) > 0
        assert all("admin@example.com" in email.sender for email in emails)
        assert count is not None

    def test_get_emails_by_sender_partial(self):
        """Test getting emails by partial sender match."""
        emails, _ = self.queries.get_emails_by_sender(
            "admin",
            options=QueryOptions(limit=10),
            partial_match=True
        )

        assert len(emails) > 0
        assert all("admin" in email.sender.lower() for email in emails)

    def test_get_emails_by_date_range(self):
        """Test getting emails by date range."""
        # Get emails from today
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)

        emails, count = self.queries.get_emails_by_date_range(
            today.isoformat(),
            tomorrow.isoformat(),
            options=QueryOptions(limit=10, include_count=True)
        )

        assert len(emails) > 0
        assert count is not None

    def test_get_emails_with_filters(self):
        """Test getting emails with additional filters."""
        filters = [
            QueryFilter(field="has_attachments", operator="=", value=1, logical_operator="AND")
        ]

        emails, _ = self.queries.get_emails_by_priority(
            min_priority=1, max_priority=5,
            options=QueryOptions(limit=10),
            filters=filters
        )

        assert len(emails) > 0
        assert all(email.has_attachments for email in emails)

    def test_get_emails_with_query_options(self):
        """Test query options (sorting, pagination)."""
        # Test sorting
        options = QueryOptions(
            limit=5,
            order_by="priority_score",
            order_direction="DESC"
        )

        emails, _ = self.queries.get_emails_by_priority(
            min_priority=1, max_priority=5,
            options=options
        )

        assert len(emails) <= 5
        # Check if sorted by priority (descending)
        for i in range(len(emails) - 1):
            assert emails[i].priority_score >= emails[i + 1].priority_score

    def test_get_email_statistics(self):
        """Test getting email statistics."""
        stats = self.queries.get_email_statistics()

        assert isinstance(stats, dict)
        assert "total_emails" in stats
        assert "priority_distribution" in stats
        assert "urgency_distribution" in stats
        assert "emails_with_attachments" in stats
        assert "unread_emails" in stats
        assert "flagged_emails" in stats
        assert "recent_emails" in stats
        assert "attachment_rate" in stats
        assert "unread_rate" in stats

        # Check that values are reasonable
        assert stats["total_emails"] > 0
        assert stats["total_emails"] == 5  # We inserted 5 test emails
        assert isinstance(stats["priority_distribution"], dict)
        assert isinstance(stats["urgency_distribution"], dict)

    def test_get_top_senders(self):
        """Test getting top senders."""
        senders = self.queries.get_top_senders(limit=5)

        assert isinstance(senders, list)
        assert len(senders) <= 5
        if senders:
            for sender in senders:
                assert "sender" in sender
                assert "email_count" in sender
                assert "last_email_date" in sender
                assert isinstance(sender["email_count"], int)
                assert sender["email_count"] > 0

    def test_query_options_pagination(self):
        """Test query pagination."""
        # Get first page
        emails_page1, _ = self.queries.get_emails_by_priority(
            min_priority=1, max_priority=5,
            options=QueryOptions(limit=2, offset=0)
        )

        # Get second page
        emails_page2, _ = self.queries.get_emails_by_priority(
            min_priority=1, max_priority=5,
            options=QueryOptions(limit=2, offset=2)
        )

        # Should not have overlapping results
        email_ids_page1 = {email.id for email in emails_page1}
        email_ids_page2 = {email.id for email in emails_page2}

        assert len(email_ids_page1.intersection(email_ids_page2)) == 0

    def test_email_summary_structure(self):
        """Test that EmailSummary has correct structure."""
        emails, _ = self.queries.get_emails_by_priority(
            min_priority=1, max_priority=5,
            options=QueryOptions(limit=1)
        )

        if emails:
            email = emails[0]
            assert hasattr(email, 'id')
            assert hasattr(email, 'message_id')
            assert hasattr(email, 'subject')
            assert hasattr(email, 'sender')
            assert hasattr(email, 'recipients')
            assert hasattr(email, 'received_at')
            assert hasattr(email, 'has_attachments')
            assert hasattr(email, 'is_read')
            assert hasattr(email, 'is_flagged')
            assert hasattr(email, 'priority_score')
            assert hasattr(email, 'urgency_level')
            assert hasattr(email, 'importance_level')
            assert hasattr(email, 'confidence_score')
            assert hasattr(email, 'attachment_count')
            assert hasattr(email, 'tag_count')

            # Check types
            assert isinstance(email.id, int)
            assert isinstance(email.message_id, str)
            assert isinstance(email.subject, str)
            assert isinstance(email.sender, str)
            assert isinstance(email.recipients, str)
            assert isinstance(email.has_attachments, bool)
            assert isinstance(email.is_read, bool)
            assert isinstance(email.is_flagged, bool)
            assert isinstance(email.priority_score, int)
            assert isinstance(email.urgency_level, str)
            assert isinstance(email.importance_level, str)
            assert isinstance(email.confidence_score, float)
            assert isinstance(email.attachment_count, int)
            assert isinstance(email.tag_count, int)

    def test_email_detail_structure(self):
        """Test that EmailDetail has correct structure."""
        emails, _ = self.queries.get_emails_by_priority(
            min_priority=1, max_priority=5,
            options=QueryOptions(limit=1)
        )

        if emails:
            email_id = emails[0].id
            detail = self.queries.get_email_by_id(email_id)

            assert detail is not None
            assert hasattr(detail, 'id')
            assert hasattr(detail, 'message_id')
            assert hasattr(detail, 'subject')
            assert hasattr(detail, 'sender')
            assert hasattr(detail, 'recipients')
            assert hasattr(detail, 'cc')
            assert hasattr(detail, 'bcc')
            assert hasattr(detail, 'body_text')
            assert hasattr(detail, 'body_html')
            assert hasattr(detail, 'received_at')
            assert hasattr(detail, 'sent_at')
            assert hasattr(detail, 'size_bytes')
            assert hasattr(detail, 'has_attachments')
            assert hasattr(detail, 'is_read')
            assert hasattr(detail, 'is_flagged')
            assert hasattr(detail, 'created_at')
            assert hasattr(detail, 'updated_at')

            # Classification data
            assert hasattr(detail, 'priority_score')
            assert hasattr(detail, 'urgency_level')
            assert hasattr(detail, 'importance_level')
            assert hasattr(detail, 'classification_type')
            assert hasattr(detail, 'confidence_score')
            assert hasattr(detail, 'ai_analysis')
            assert hasattr(detail, 'classified_at')

            # Related data
            assert hasattr(detail, 'attachments')
            assert hasattr(detail, 'tags')
            assert hasattr(detail, 'history')

            # Check that related data are lists
            assert isinstance(detail.attachments, list)
            assert isinstance(detail.tags, list)
            assert isinstance(detail.history, list)

    def test_query_filter_combinations(self):
        """Test combining multiple query filters."""
        filters = [
            QueryFilter(field="has_attachments", operator="=", value=1, logical_operator="AND"),
            QueryFilter(field="is_flagged", operator="=", value=0, logical_operator="AND")
        ]

        emails, _ = self.queries.get_emails_by_priority(
            min_priority=1, max_priority=5,
            options=QueryOptions(limit=10),
            filters=filters
        )

        assert len(emails) >= 0  # Should not crash
        for email in emails:
            assert email.has_attachments is True
            assert email.is_flagged is False

    def test_empty_result_handling(self):
        """Test handling of empty results."""
        # Search for emails with impossible criteria
        emails, count = self.queries.get_emails_by_priority(
            min_priority=10, max_priority=20,  # Impossible range
            options=QueryOptions(limit=10, include_count=True)
        )

        assert len(emails) == 0
        assert count == 0