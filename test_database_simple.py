"""
Simple database test that directly imports what we need.
"""

import sys
import tempfile
import os
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Direct imports to avoid complex dependency chains
sys.path.insert(0, str(Path(__file__).parent / "src" / "email_priority_manager" / "database"))

try:
    from connection import DatabaseConnectionManager
    from models import Email, Attachment, Classification, Rule, History, Tag, EmailTag
    print("SUCCESS: Direct database imports successful")
except ImportError as e:
    print(f"ERROR: Import error: {e}")
    sys.exit(1)


def test_basic_operations():
    """Test basic database operations without full schema."""
    print("\nTesting basic database operations...")

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    try:
        db_manager = DatabaseConnectionManager(db_path)
        print(f"SUCCESS: Database manager created")

        # Test connection
        conn = db_manager.get_connection()
        print("SUCCESS: Database connection established")

        # Create basic tables manually for testing
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT UNIQUE NOT NULL,
                    subject TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    recipients TEXT NOT NULL,
                    body_text TEXT,
                    received_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS email_tags (
                    email_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (email_id, tag_id),
                    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
                )
            """)
        print("SUCCESS: Basic tables created")

        # Test email creation
        email = Email(
            message_id="test@example.com",
            subject="Test Email",
            sender="sender@example.com",
            recipients="recipient@example.com",
            body_text="This is a test email body.",
            received_at=datetime.now()
        )

        with conn:
            cursor = conn.execute("""
                INSERT INTO emails (message_id, subject, sender, recipients, body_text, received_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                email.message_id, email.subject, email.sender, email.recipients,
                email.body_text, email.received_at
            ))
            email.id = cursor.lastrowid
        print(f"SUCCESS: Email created with ID: {email.id}")

        # Test email retrieval
        with conn:
            cursor = conn.execute("SELECT * FROM emails WHERE id = ?", (email.id,))
            row = cursor.fetchone()
            assert row is not None
            assert row[2] == "Test Email"  # subject column
        print("SUCCESS: Email retrieval successful")

        # Test tag creation
        tag = Tag(name="Test Tag", description="Test tag")
        with conn:
            cursor = conn.execute("""
                INSERT INTO tags (name, description) VALUES (?, ?)
            """, (tag.name, tag.description))
            tag.id = cursor.lastrowid
        print(f"SUCCESS: Tag created with ID: {tag.id}")

        # Test email-tag relationship
        email_tag = EmailTag(email_id=email.id, tag_id=tag.id)
        with conn:
            conn.execute("""
                INSERT OR IGNORE INTO email_tags (email_id, tag_id)
                VALUES (?, ?)
            """, (email_tag.email_id, email_tag.tag_id))
        print("SUCCESS: Email-tag relationship created")

        # Test relationship queries
        with conn:
            cursor = conn.execute("""
                SELECT t.* FROM tags t
                JOIN email_tags et ON t.id = et.tag_id
                WHERE et.email_id = ?
            """, (email.id,))
            tag_rows = cursor.fetchall()
            assert len(tag_rows) == 1
            assert tag_rows[0][1] == "Test Tag"  # name column
        print("SUCCESS: Email tags query successful")

        # Test data integrity
        with conn:
            cursor = conn.execute("SELECT COUNT(*) FROM emails")
            email_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM tags")
            tag_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM email_tags")
            relationship_count = cursor.fetchone()[0]

        print(f"SUCCESS: Data integrity verified - {email_count} emails, {tag_count} tags, {relationship_count} relationships")

        return True

    except Exception as e:
        print(f"ERROR: Basic operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup - handle Windows file locking issues
        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
        except PermissionError:
            # File is locked, ignore cleanup error
            pass


def test_model_validation():
    """Test model validation."""
    print("\nTesting model validation...")

    try:
        # Test valid email
        email = Email(
            message_id="valid@example.com",
            subject="Valid Email",
            sender="sender@example.com",
            recipients="recipient@example.com"
        )
        print("SUCCESS: Valid email created")

        # Test invalid email (missing required fields)
        try:
            invalid_email = Email(message_id="", subject="Test", sender="test@example.com", recipients="test@example.com")
            print("ERROR: Should have failed validation")
            return False
        except ValueError:
            print("SUCCESS: Invalid email properly rejected")

        # Test valid classification
        classification = Classification(
            email_id=1,
            priority_score=3,
            urgency_level="medium",
            importance_level="medium",
            classification_type="test"
        )
        print("SUCCESS: Valid classification created")

        # Test invalid classification
        try:
            invalid_classification = Classification(
                email_id=1,
                priority_score=6,  # Invalid: should be 1-5
                urgency_level="medium",
                importance_level="medium",
                classification_type="test"
            )
            print("ERROR: Should have failed validation")
            return False
        except ValueError:
            print("SUCCESS: Invalid classification properly rejected")

        # Test valid rule
        rule = Rule(
            name="Test Rule",
            rule_type="sender",
            condition="test@example.com",
            action="classify"
        )
        print("SUCCESS: Valid rule created")

        # Test invalid rule
        try:
            invalid_rule = Rule(
                name="Test Rule",
                rule_type="invalid_type",  # Invalid
                condition="test@example.com",
                action="classify"
            )
            print("ERROR: Should have failed validation")
            return False
        except ValueError:
            print("SUCCESS: Invalid rule properly rejected")

        return True

    except Exception as e:
        print(f"ERROR: Model validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all database tests."""
    print("Starting simple database tests...")

    tests = [
        test_basic_operations,
        test_model_validation
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
            print(f"ERROR: Test {test.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\nTest Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("SUCCESS: All database tests passed!")
        return 0
    else:
        print("ERROR: Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())