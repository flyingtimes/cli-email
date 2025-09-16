"""
Comprehensive tests for database operations.
Tests all CRUD operations, relationships, and data integrity.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from src.email_priority_manager.database import (
    Email, Attachment, Classification, Rule, History, Tag, EmailTag,
    DatabaseConnectionManager, get_db_manager,
    EmailOperations, AttachmentOperations, ClassificationOperations,
    RuleOperations, HistoryOperations, TagOperations, EmailTagOperations,
    DatabaseOperations, create_database, get_migration_status,
    DatabaseQueryError, DatabaseConnectionError
)


@pytest.fixture
def temp_db_path():
    """Create a temporary database path for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def db_manager(temp_db_path):
    """Create a database manager for testing."""
    return DatabaseConnectionManager(temp_db_path)


@pytest.fixture
def ops(db_manager):
    """Create database operations for testing."""
    return DatabaseOperations(db_manager)


@pytest.fixture
def sample_email():
    """Create a sample email for testing."""
    return Email(
        message_id="test@example.com",
        subject="Test Email",
        sender="sender@example.com",
        recipients="recipient@example.com",
        body_text="This is a test email body.",
        received_at=datetime.now()
    )


@pytest.fixture
def sample_attachment():
    """Create a sample attachment for testing."""
    return Attachment(
        email_id=1,
        filename="test.pdf",
        file_path="/path/to/test.pdf",
        size_bytes=1024,
        mime_type="application/pdf"
    )


@pytest.fixture
def sample_classification():
    """Create a sample classification for testing."""
    return Classification(
        email_id=1,
        priority_score=4,
        urgency_level="high",
        importance_level="medium",
        classification_type="ai",
        confidence_score=0.85,
        ai_analysis="This email appears to be important."
    )


@pytest.fixture
def sample_rule():
    """Create a sample rule for testing."""
    return Rule(
        name="Test Rule",
        description="Test rule for testing",
        rule_type="sender",
        condition="test@example.com",
        action="classify",
        priority=5
    )


@pytest.fixture
def sample_tag():
    """Create a sample tag for testing."""
    return Tag(
        name="Test Tag",
        description="Test tag for testing",
        color="#FF0000"
    )


class TestDatabaseConnection:
    """Test database connection functionality."""

    def test_create_database_manager(self, temp_db_path):
        """Test creating database manager."""
        db_manager = DatabaseConnectionManager(temp_db_path)
        assert db_manager.db_path == temp_db_path
        assert not db_manager.database_exists()

    def test_connection_creation(self, db_manager):
        """Test database connection creation."""
        conn = db_manager.get_connection()
        assert conn is not None
        assert db_manager.database_exists()

    def test_transaction_management(self, db_manager):
        """Test transaction management."""
        with db_manager.transaction() as conn:
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
            conn.execute("INSERT INTO test (id) VALUES (1)")

        # Verify data was committed
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM test")
            assert cursor.fetchone()[0] == 1

    def test_transaction_rollback(self, db_manager):
        """Test transaction rollback on error."""
        try:
            with db_manager.transaction() as conn:
                conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
                conn.execute("INSERT INTO test (id) VALUES (1)")
                raise Exception("Test error")
        except Exception:
            pass

        # Verify data was rolled back
        with db_manager.get_cursor() as cursor:
            # Table should not exist due to rollback
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test'")
            assert cursor.fetchone() is None

    def test_database_statistics(self, db_manager):
        """Test database statistics."""
        stats = db_manager.get_connection_stats()
        assert 'database_path' in stats
        assert 'database_exists' in stats
        assert 'database_size_bytes' in stats
        assert stats['database_path'] == db_manager.db_path


class TestEmailOperations:
    """Test email operations."""

    def test_create_email(self, ops, sample_email):
        """Test creating an email."""
        email = ops.emails.create(sample_email)
        assert email.id is not None
        assert email.subject == sample_email.subject
        assert email.sender == sample_email.sender

    def test_get_email_by_id(self, ops, sample_email):
        """Test getting email by ID."""
        created = ops.emails.create(sample_email)
        retrieved = ops.emails.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.subject == created.subject

    def test_get_email_by_message_id(self, ops, sample_email):
        """Test getting email by message ID."""
        created = ops.emails.create(sample_email)
        retrieved = ops.emails.get_by_message_id(sample_email.message_id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.message_id == sample_email.message_id

    def test_update_email(self, ops, sample_email):
        """Test updating an email."""
        created = ops.emails.create(sample_email)
        created.subject = "Updated Subject"
        created.is_read = True

        updated = ops.emails.update(created)
        assert updated.subject == "Updated Subject"
        assert updated.is_read is True

    def test_delete_email(self, ops, sample_email):
        """Test deleting an email."""
        created = ops.emails.create(sample_email)
        email_id = created.id

        deleted = ops.emails.delete(email_id)
        assert deleted is True

        retrieved = ops.emails.get_by_id(email_id)
        assert retrieved is None

    def test_get_all_emails(self, ops):
        """Test getting all emails."""
        # Create multiple emails
        for i in range(5):
            email = Email(
                message_id=f"test{i}@example.com",
                subject=f"Test Email {i}",
                sender=f"sender{i}@example.com",
                recipients=f"recipient{i}@example.com"
            )
            ops.emails.create(email)

        emails = ops.emails.get_all()
        assert len(emails) == 5

        # Test pagination
        first_two = ops.emails.get_all(limit=2)
        assert len(first_two) == 2

    def test_email_count(self, ops):
        """Test email count."""
        # Initially should be 0
        assert ops.emails.count() == 0

        # Create some emails
        for i in range(3):
            email = Email(
                message_id=f"test{i}@example.com",
                subject=f"Test Email {i}",
                sender=f"sender{i}@example.com",
                recipients=f"recipient{i}@example.com"
            )
            ops.emails.create(email)

        assert ops.emails.count() == 3

    def test_duplicate_message_id_error(self, ops, sample_email):
        """Test error on duplicate message ID."""
        ops.emails.create(sample_email)

        # Try to create another email with same message_id
        with pytest.raises(DatabaseQueryError):
            ops.emails.create(sample_email)


class TestAttachmentOperations:
    """Test attachment operations."""

    def test_create_attachment(self, ops, sample_email, sample_attachment):
        """Test creating an attachment."""
        email = ops.emails.create(sample_email)
        sample_attachment.email_id = email.id

        attachment = ops.attachments.create(sample_attachment)
        assert attachment.id is not None
        assert attachment.email_id == email.id
        assert attachment.filename == sample_attachment.filename

    def test_get_attachment_by_id(self, ops, sample_email, sample_attachment):
        """Test getting attachment by ID."""
        email = ops.emails.create(sample_email)
        sample_attachment.email_id = email.id

        created = ops.attachments.create(sample_attachment)
        retrieved = ops.attachments.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.filename == created.filename

    def test_get_attachments_by_email_id(self, ops, sample_email):
        """Test getting attachments by email ID."""
        email = ops.emails.create(sample_email)

        # Create multiple attachments
        for i in range(3):
            attachment = Attachment(
                email_id=email.id,
                filename=f"file{i}.pdf",
                file_path=f"/path/to/file{i}.pdf",
                size_bytes=1024 * (i + 1)
            )
            ops.attachments.create(attachment)

        attachments = ops.attachments.get_by_email_id(email.id)
        assert len(attachments) == 3

    def test_delete_attachment(self, ops, sample_email, sample_attachment):
        """Test deleting an attachment."""
        email = ops.emails.create(sample_email)
        sample_attachment.email_id = email.id

        created = ops.attachments.create(sample_attachment)
        attachment_id = created.id

        deleted = ops.attachments.delete(attachment_id)
        assert deleted is True

        retrieved = ops.attachments.get_by_id(attachment_id)
        assert retrieved is None


class TestClassificationOperations:
    """Test classification operations."""

    def test_create_classification(self, ops, sample_email, sample_classification):
        """Test creating a classification."""
        email = ops.emails.create(sample_email)
        sample_classification.email_id = email.id

        classification = ops.classifications.create(sample_classification)
        assert classification.id is not None
        assert classification.email_id == email.id
        assert classification.priority_score == sample_classification.priority_score

    def test_get_classification_by_id(self, ops, sample_email, sample_classification):
        """Test getting classification by ID."""
        email = ops.emails.create(sample_email)
        sample_classification.email_id = email.id

        created = ops.classifications.create(sample_classification)
        retrieved = ops.classifications.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.priority_score == created.priority_score

    def test_get_classification_by_email_id(self, ops, sample_email, sample_classification):
        """Test getting classification by email ID."""
        email = ops.emails.create(sample_email)
        sample_classification.email_id = email.id

        created = ops.classifications.create(sample_classification)
        retrieved = ops.classifications.get_by_email_id(email.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_update_classification(self, ops, sample_email, sample_classification):
        """Test updating a classification."""
        email = ops.emails.create(sample_email)
        sample_classification.email_id = email.id

        created = ops.classifications.create(sample_classification)
        created.priority_score = 5
        created.urgency_level = "critical"

        updated = ops.classifications.update(created)
        assert updated.priority_score == 5
        assert updated.urgency_level == "critical"

    def test_get_classifications_by_priority(self, ops, sample_email):
        """Test getting classifications by priority."""
        email = ops.emails.create(sample_email)

        # Create classifications with different priorities
        for priority in range(1, 6):
            classification = Classification(
                email_id=email.id,
                priority_score=priority,
                urgency_level="medium",
                importance_level="medium",
                classification_type="test"
            )
            ops.classifications.create(classification)

        # Get classifications with priority 3
        priority_3 = ops.classifications.get_by_priority(3)
        assert len(priority_3) == 1
        assert priority_3[0].priority_score == 3

    def test_get_classifications_by_urgency(self, ops, sample_email):
        """Test getting classifications by urgency level."""
        email = ops.emails.create(sample_email)

        # Create classifications with different urgency levels
        urgency_levels = ['low', 'medium', 'high', 'critical']
        for urgency in urgency_levels:
            classification = Classification(
                email_id=email.id,
                priority_score=3,
                urgency_level=urgency,
                importance_level="medium",
                classification_type="test"
            )
            ops.classifications.create(classification)

        # Get high urgency classifications
        high_urgency = ops.classifications.get_by_urgency('high')
        assert len(high_urgency) == 1
        assert high_urgency[0].urgency_level == 'high'

    def test_duplicate_classification_error(self, ops, sample_email, sample_classification):
        """Test error on duplicate classification for same email."""
        email = ops.emails.create(sample_email)
        sample_classification.email_id = email.id

        ops.classifications.create(sample_classification)

        # Try to create another classification for same email
        with pytest.raises(DatabaseQueryError):
            ops.classifications.create(sample_classification)


class TestRuleOperations:
    """Test rule operations."""

    def test_create_rule(self, ops, sample_rule):
        """Test creating a rule."""
        rule = ops.rules.create(sample_rule)
        assert rule.id is not None
        assert rule.name == sample_rule.name
        assert rule.condition == sample_rule.condition

    def test_get_rule_by_id(self, ops, sample_rule):
        """Test getting rule by ID."""
        created = ops.rules.create(sample_rule)
        retrieved = ops.rules.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    def test_get_all_rules(self, ops):
        """Test getting all rules."""
        # Create multiple rules
        for i in range(3):
            rule = Rule(
                name=f"Test Rule {i}",
                rule_type="sender",
                condition=f"test{i}@example.com",
                action="classify",
                priority=i
            )
            ops.rules.create(rule)

        rules = ops.rules.get_all()
        assert len(rules) == 3

        # Test active only
        all_rules = ops.rules.get_all(active_only=False)
        active_rules = ops.rules.get_all(active_only=True)
        assert len(all_rules) >= len(active_rules)

    def test_update_rule(self, ops, sample_rule):
        """Test updating a rule."""
        created = ops.rules.create(sample_rule)
        created.name = "Updated Rule"
        created.is_active = False

        updated = ops.rules.update(created)
        assert updated.name == "Updated Rule"
        assert updated.is_active is False

    def test_delete_rule(self, ops, sample_rule):
        """Test deleting a rule."""
        created = ops.rules.create(sample_rule)
        rule_id = created.id

        deleted = ops.rules.delete(rule_id)
        assert deleted is True

        retrieved = ops.rules.get_by_id(rule_id)
        assert retrieved is None


class TestTagOperations:
    """Test tag operations."""

    def test_create_tag(self, ops, sample_tag):
        """Test creating a tag."""
        tag = ops.tags.create(sample_tag)
        assert tag.id is not None
        assert tag.name == sample_tag.name
        assert tag.color == sample_tag.color

    def test_get_tag_by_id(self, ops, sample_tag):
        """Test getting tag by ID."""
        created = ops.tags.create(sample_tag)
        retrieved = ops.tags.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    def test_get_tag_by_name(self, ops, sample_tag):
        """Test getting tag by name."""
        created = ops.tags.create(sample_tag)
        retrieved = ops.tags.get_by_name(sample_tag.name)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == sample_tag.name

    def test_get_all_tags(self, ops):
        """Test getting all tags."""
        # Create multiple tags
        for i in range(3):
            tag = Tag(
                name=f"Test Tag {i}",
                description=f"Test tag {i}",
                color=f"#FF000{i}"
            )
            ops.tags.create(tag)

        tags = ops.tags.get_all()
        assert len(tags) == 3

    def test_update_tag(self, ops, sample_tag):
        """Test updating a tag."""
        created = ops.tags.create(sample_tag)
        created.name = "Updated Tag"
        created.description = "Updated description"

        updated = ops.tags.update(created)
        assert updated.name == "Updated Tag"
        assert updated.description == "Updated description"

    def test_delete_tag(self, ops, sample_tag):
        """Test deleting a tag."""
        created = ops.tags.create(sample_tag)
        tag_id = created.id

        deleted = ops.tags.delete(tag_id)
        assert deleted is True

        retrieved = ops.tags.get_by_id(tag_id)
        assert retrieved is None

    def test_duplicate_tag_name_error(self, ops, sample_tag):
        """Test error on duplicate tag name."""
        ops.tags.create(sample_tag)

        # Try to create another tag with same name
        with pytest.raises(DatabaseQueryError):
            ops.tags.create(sample_tag)


class TestEmailTagOperations:
    """Test email-tag relationship operations."""

    def test_create_email_tag_relationship(self, ops, sample_email, sample_tag):
        """Test creating email-tag relationship."""
        email = ops.emails.create(sample_email)
        tag = ops.tags.create(sample_tag)

        email_tag = EmailTag(email_id=email.id, tag_id=tag.id)
        relationship = ops.email_tags.create(email_tag)
        assert relationship.email_id == email.id
        assert relationship.tag_id == tag.id

    def test_get_email_tags(self, ops, sample_email):
        """Test getting tags for an email."""
        email = ops.emails.create(sample_email)

        # Create multiple tags and assign them to email
        tag_ids = []
        for i in range(3):
            tag = Tag(name=f"Tag {i}", description=f"Tag {i}")
            created_tag = ops.tags.create(tag)
            tag_ids.append(created_tag.id)

            email_tag = EmailTag(email_id=email.id, tag_id=created_tag.id)
            ops.email_tags.create(email_tag)

        email_tags = ops.email_tags.get_email_tags(email.id)
        assert len(email_tags) == 3
        tag_names = [tag.name for tag in email_tags]
        assert "Tag 0" in tag_names
        assert "Tag 1" in tag_names
        assert "Tag 2" in tag_names

    def test_get_tag_emails(self, ops, sample_tag):
        """Test getting emails for a tag."""
        tag = ops.tags.create(sample_tag)

        # Create multiple emails and assign them to tag
        email_ids = []
        for i in range(3):
            email = Email(
                message_id=f"test{i}@example.com",
                subject=f"Test Email {i}",
                sender=f"sender{i}@example.com",
                recipients=f"recipient{i}@example.com"
            )
            created_email = ops.emails.create(email)
            email_ids.append(created_email.id)

            email_tag = EmailTag(email_id=created_email.id, tag_id=tag.id)
            ops.email_tags.create(email_tag)

        tag_emails = ops.email_tags.get_tag_emails(tag.id)
        assert len(tag_emails) == 3
        email_subjects = [email.subject for email in tag_emails]
        assert "Test Email 0" in email_subjects
        assert "Test Email 1" in email_subjects
        assert "Test Email 2" in email_subjects

    def test_delete_email_tag_relationship(self, ops, sample_email, sample_tag):
        """Test deleting email-tag relationship."""
        email = ops.emails.create(sample_email)
        tag = ops.tags.create(sample_tag)

        email_tag = EmailTag(email_id=email.id, tag_id=tag.id)
        ops.email_tags.create(email_tag)

        deleted = ops.email_tags.delete(email.id, tag.id)
        assert deleted is True

        # Verify relationship is deleted
        email_tags = ops.email_tags.get_email_tags(email.id)
        assert len(email_tags) == 0

    def test_duplicate_relationship_ignored(self, ops, sample_email, sample_tag):
        """Test that duplicate relationships are ignored."""
        email = ops.emails.create(sample_email)
        tag = ops.tags.create(sample_tag)

        email_tag = EmailTag(email_id=email.id, tag_id=tag.id)

        # Create same relationship twice
        ops.email_tags.create(email_tag)
        ops.email_tags.create(email_tag)

        # Should only have one relationship
        email_tags = ops.email_tags.get_email_tags(email.id)
        assert len(email_tags) == 1


class TestDatabaseOperations:
    """Test database operations container."""

    def test_get_statistics(self, ops):
        """Test getting database statistics."""
        # Initially should have basic stats
        stats = ops.get_statistics()
        assert 'total_emails' in stats
        assert 'total_attachments' in stats
        assert 'classified_emails' in stats
        assert 'total_tags' in stats
        assert 'active_rules' in stats
        assert 'database_size' in stats

        # Initially should be mostly empty
        assert stats['total_emails'] == 0
        assert stats['total_attachments'] == 0
        assert stats['classified_emails'] == 0

    def test_full_workflow(self, ops):
        """Test complete workflow with all operations."""
        # Create email
        email = Email(
            message_id="workflow@example.com",
            subject="Workflow Test",
            sender="sender@example.com",
            recipients="recipient@example.com",
            body_text="Testing complete workflow"
        )
        created_email = ops.emails.create(email)

        # Create attachment
        attachment = Attachment(
            email_id=created_email.id,
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            size_bytes=2048
        )
        ops.attachments.create(attachment)

        # Create classification
        classification = Classification(
            email_id=created_email.id,
            priority_score=4,
            urgency_level="high",
            importance_level="high",
            classification_type="test",
            confidence_score=0.9
        )
        ops.classifications.create(classification)

        # Create tag and assign to email
        tag = Tag(name="Workflow", description="Workflow test tag")
        created_tag = ops.tags.create(tag)

        email_tag = EmailTag(email_id=created_email.id, tag_id=created_tag.id)
        ops.email_tags.create(email_tag)

        # Create rule
        rule = Rule(
            name="Workflow Rule",
            rule_type="sender",
            condition="sender@example.com",
            action="classify"
        )
        ops.rules.create(rule)

        # Create history entry
        history = History(
            email_id=created_email.id,
            action_type="test",
            action_details="Workflow test completed"
        )
        ops.history.create(history)

        # Verify all data was created
        assert ops.emails.count() == 1
        assert len(ops.attachments.get_by_email_id(created_email.id)) == 1
        assert ops.classifications.get_by_email_id(created_email.id) is not None
        assert len(ops.email_tags.get_email_tags(created_email.id)) == 1
        assert len(ops.rules.get_all()) == 1
        assert len(ops.history.get_by_email_id(created_email.id)) == 1

        # Get statistics
        stats = ops.get_statistics()
        assert stats['total_emails'] == 1
        assert stats['total_attachments'] == 1
        assert stats['classified_emails'] == 1
        assert stats['total_tags'] == 1
        assert stats['active_rules'] == 1


class TestFullTextSearch:
    """Test full-text search functionality."""

    def test_search_emails(self, ops):
        """Test searching emails with full-text search."""
        # Create test emails
        emails = [
            Email(
                message_id="urgent@example.com",
                subject="Urgent Meeting Tomorrow",
                sender="boss@example.com",
                recipients="employee@example.com",
                body_text="Please attend the urgent meeting tomorrow at 2 PM."
            ),
            Email(
                message_id="project@example.com",
                subject="Project Update",
                sender="manager@example.com",
                recipients="team@example.com",
                body_text="The project is progressing well and will be completed on time."
            ),
            Email(
                message_id="holiday@example.com",
                subject="Holiday Schedule",
                sender="hr@example.com",
                recipients="all@example.com",
                body_text="Please note the upcoming holiday schedule for next month."
            )
        ]

        for email in emails:
            ops.emails.create(email)

        # Test search
        results = ops.emails.search("urgent meeting")
        assert len(results) == 1
        assert "Urgent Meeting Tomorrow" in results[0].subject

        # Test search by sender
        results = ops.emails.search("boss@example.com")
        assert len(results) == 1
        assert results[0].sender == "boss@example.com"

        # Test search in body
        results = ops.emails.search("project progressing")
        assert len(results) == 1
        assert "Project Update" in results[0].subject

        # Test search with no results
        results = ops.emails.search("nonexistent term")
        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])