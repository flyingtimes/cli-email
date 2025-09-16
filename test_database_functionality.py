"""
Simple database functionality test script.
Tests basic database operations without pytest dependencies.
"""

import sys
import tempfile
import os
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from email_priority_manager.database import (
        Email, Attachment, Classification, Rule, History, Tag, EmailTag,
        DatabaseConnectionManager,
        EmailOperations, AttachmentOperations, ClassificationOperations,
        RuleOperations, HistoryOperations, TagOperations, EmailTagOperations,
        DatabaseOperations,
        DatabaseQueryError, DatabaseConnectionError
    )
    print("✅ Database imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def test_database_connection():
    """Test basic database connection."""
    print("\n🔍 Testing database connection...")

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    try:
        db_manager = DatabaseConnectionManager(db_path)
        print(f"✅ Database manager created: {db_path}")

        # Test connection
        conn = db_manager.get_connection()
        print("✅ Database connection established")

        # Test basic operations
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
        print("✅ Basic database query successful")

        # Test transaction
        with db_manager.transaction() as conn:
            conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
            conn.execute("INSERT INTO test_table (id, name) VALUES (1, 'test')")
        print("✅ Transaction management successful")

        # Verify data persistence
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT name FROM test_table WHERE id = 1")
            result = cursor.fetchone()
            assert result[0] == 'test'
        print("✅ Data persistence verified")

        return True

    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_email_operations():
    """Test email CRUD operations."""
    print("\n🔍 Testing email operations...")

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    try:
        db_manager = DatabaseConnectionManager(db_path)
        ops = DatabaseOperations(db_manager)

        # Create email
        email = Email(
            message_id="test@example.com",
            subject="Test Email",
            sender="sender@example.com",
            recipients="recipient@example.com",
            body_text="This is a test email body.",
            received_at=datetime.now()
        )

        created_email = ops.emails.create(email)
        print(f"✅ Email created with ID: {created_email.id}")

        # Retrieve email
        retrieved_email = ops.emails.get_by_id(created_email.id)
        assert retrieved_email is not None
        assert retrieved_email.subject == "Test Email"
        print("✅ Email retrieval successful")

        # Update email
        created_email.subject = "Updated Test Email"
        created_email.is_read = True
        updated_email = ops.emails.update(created_email)
        assert updated_email.subject == "Updated Test Email"
        assert updated_email.is_read is True
        print("✅ Email update successful")

        # Search email
        emails = ops.emails.search("Updated Test")
        assert len(emails) == 1
        print("✅ Email search successful")

        # Count emails
        count = ops.emails.count()
        assert count == 1
        print(f"✅ Email count: {count}")

        # Delete email
        deleted = ops.emails.delete(created_email.id)
        assert deleted is True
        print("✅ Email deletion successful")

        # Verify deletion
        count = ops.emails.count()
        assert count == 0
        print("✅ Email deletion verified")

        return True

    except Exception as e:
        print(f"❌ Email operations test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_relationship_operations():
    """Test database relationships."""
    print("\n🔍 Testing relationship operations...")

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    try:
        db_manager = DatabaseConnectionManager(db_path)
        ops = DatabaseOperations(db_manager)

        # Create email
        email = Email(
            message_id="rel_test@example.com",
            subject="Relationship Test",
            sender="sender@example.com",
            recipients="recipient@example.com"
        )
        created_email = ops.emails.create(email)

        # Create tag
        tag = Tag(name="Test Tag", description="Test tag for relationships")
        created_tag = ops.tags.create(tag)

        # Create email-tag relationship
        email_tag = EmailTag(email_id=created_email.id, tag_id=created_tag.id)
        ops.email_tags.create(email_tag)
        print("✅ Email-tag relationship created")

        # Test getting email tags
        email_tags = ops.email_tags.get_email_tags(created_email.id)
        assert len(email_tags) == 1
        assert email_tags[0].name == "Test Tag"
        print("✅ Email tags retrieval successful")

        # Test getting tag emails
        tag_emails = ops.email_tags.get_tag_emails(created_tag.id)
        assert len(tag_emails) == 1
        assert tag_emails[0].subject == "Relationship Test"
        print("✅ Tag emails retrieval successful")

        # Test classification
        classification = Classification(
            email_id=created_email.id,
            priority_score=4,
            urgency_level="high",
            importance_level="medium",
            classification_type="test",
            confidence_score=0.9
        )
        ops.classifications.create(classification)
        print("✅ Classification created")

        # Test attachment
        attachment = Attachment(
            email_id=created_email.id,
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            size_bytes=1024
        )
        ops.attachments.create(attachment)
        print("✅ Attachment created")

        # Test rule
        rule = Rule(
            name="Test Rule",
            rule_type="sender",
            condition="sender@example.com",
            action="classify"
        )
        ops.rules.create(rule)
        print("✅ Rule created")

        # Test history
        history = History(
            email_id=created_email.id,
            action_type="test",
            action_details="Test relationship operations"
        )
        ops.history.create(history)
        print("✅ History entry created")

        # Get statistics
        stats = ops.get_statistics()
        assert stats['total_emails'] == 1
        assert stats['total_attachments'] == 1
        assert stats['classified_emails'] == 1
        assert stats['total_tags'] == 1
        assert stats['active_rules'] == 1
        print(f"✅ Database statistics: {stats['total_emails']} emails, {stats['total_tags']} tags")

        return True

    except Exception as e:
        print(f"❌ Relationship operations test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_full_text_search():
    """Test full-text search functionality."""
    print("\n🔍 Testing full-text search...")

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    try:
        db_manager = DatabaseConnectionManager(db_path)
        ops = DatabaseOperations(db_manager)

        # Create test emails
        test_emails = [
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

        for email in test_emails:
            ops.emails.create(email)
        print(f"✅ Created {len(test_emails)} test emails")

        # Test search
        results = ops.emails.search("urgent meeting")
        assert len(results) == 1
        assert "Urgent Meeting Tomorrow" in results[0].subject
        print("✅ Search for 'urgent meeting' found 1 result")

        # Test search by sender
        results = ops.emails.search("boss@example.com")
        assert len(results) == 1
        assert results[0].sender == "boss@example.com"
        print("✅ Search by sender found 1 result")

        # Test search in body
        results = ops.emails.search("project progressing")
        assert len(results) == 1
        assert "Project Update" in results[0].subject
        print("✅ Search in body text found 1 result")

        # Test search with no results
        results = ops.emails.search("nonexistent term")
        assert len(results) == 0
        print("✅ Search for nonexistent term found 0 results")

        return True

    except Exception as e:
        print(f"❌ Full-text search test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


def main():
    """Run all database tests."""
    print("🚀 Starting database functionality tests...")

    tests = [
        test_database_connection,
        test_email_operations,
        test_relationship_operations,
        test_full_text_search
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1

    print(f"\n📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All database tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())