"""
Initial schema migration for email priority manager.
Creates all core tables and indexes.
"""

from datetime import datetime
from typing import List

from .migration_manager import Migration


class InitialSchemaMigration(Migration):
    """Initial database schema migration."""

    def __init__(self):
        super().__init__(
            version=1,
            name="initial_schema",
            description="Create all core tables and indexes for email priority manager"
        )

    def up(self) -> List[str]:
        """
        Return SQL statements to create the initial schema.

        Returns:
            List of SQL statements
        """
        return [
            # Create schema version table
            """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                );
            """,

            # Create emails table
            """
                CREATE TABLE IF NOT EXISTS emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT UNIQUE NOT NULL,
                    subject TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    recipients TEXT NOT NULL,
                    cc TEXT,
                    bcc TEXT,
                    body_text TEXT,
                    body_html TEXT,
                    received_at TIMESTAMP NOT NULL,
                    sent_at TIMESTAMP,
                    size_bytes INTEGER,
                    has_attachments BOOLEAN DEFAULT FALSE,
                    is_read BOOLEAN DEFAULT FALSE,
                    is_flagged BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """,

            # Create attachments table
            """
                CREATE TABLE IF NOT EXISTS attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    size_bytes INTEGER,
                    mime_type TEXT,
                    content_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE
                );
            """,

            # Create classifications table
            """
                CREATE TABLE IF NOT EXISTS classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id INTEGER UNIQUE NOT NULL,
                    priority_score INTEGER NOT NULL CHECK (priority_score BETWEEN 1 AND 5),
                    urgency_level TEXT NOT NULL CHECK (urgency_level IN ('low', 'medium', 'high', 'critical')),
                    importance_level TEXT NOT NULL CHECK (importance_level IN ('low', 'medium', 'high', 'critical')),
                    classification_type TEXT NOT NULL,
                    confidence_score REAL CHECK (confidence_score BETWEEN 0 AND 1),
                    ai_analysis TEXT,
                    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE
                );
            """,

            # Create rules table
            """
                CREATE TABLE IF NOT EXISTS rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    rule_type TEXT NOT NULL CHECK (rule_type IN ('sender', 'keyword', 'time', 'custom')),
                    condition TEXT NOT NULL,
                    action TEXT NOT NULL CHECK (action IN ('classify', 'tag', 'flag', 'move')),
                    priority INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """,

            # Create history table
            """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id INTEGER,
                    action_type TEXT NOT NULL,
                    action_details TEXT,
                    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE SET NULL
                );
            """,

            # Create tags table
            """
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    color TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """,

            # Create email_tags table
            """
                CREATE TABLE IF NOT EXISTS email_tags (
                    email_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (email_id, tag_id),
                    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
                );
            """,

            # Create indexes for performance
            """
                CREATE INDEX IF NOT EXISTS idx_emails_message_id ON emails(message_id);
            """,
            """
                CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender);
            """,
            """
                CREATE INDEX IF NOT EXISTS idx_emails_received_at ON emails(received_at);
            """,
            """
                CREATE INDEX IF NOT EXISTS idx_emails_has_attachments ON emails(has_attachments);
            """,
            """
                CREATE INDEX IF NOT EXISTS idx_attachments_email_id ON attachments(email_id);
            """,
            """
                CREATE INDEX IF NOT EXISTS idx_attachments_content_hash ON attachments(content_hash);
            """,
            """
                CREATE INDEX IF NOT EXISTS idx_classifications_email_id ON classifications(email_id);
            """,
            """
                CREATE INDEX IF NOT EXISTS idx_classifications_priority_score ON classifications(priority_score);
            """,
            """
                CREATE INDEX IF NOT EXISTS idx_classifications_urgency_level ON classifications(urgency_level);
            """,
            """
                CREATE INDEX IF NOT EXISTS idx_classifications_importance_level ON classifications(importance_level);
            """,
            """
                CREATE INDEX IF NOT EXISTS idx_rules_rule_type ON rules(rule_type);
            """,
            """
                CREATE INDEX IF NOT EXISTS idx_rules_is_active ON rules(is_active);
            """,
            """
                CREATE INDEX IF NOT EXISTS idx_history_email_id ON history(email_id);
            """,
            """
                CREATE INDEX IF NOT EXISTS idx_history_action_type ON history(action_type);
            """,
            """
                CREATE INDEX IF NOT EXISTS idx_history_performed_at ON history(performed_at);
            """,
            """
                CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);
            """,
            """
                CREATE INDEX IF NOT EXISTS idx_email_tags_email_id ON email_tags(email_id);
            """,
            """
                CREATE INDEX IF NOT EXISTS idx_email_tags_tag_id ON email_tags(tag_id);
            """,

            # Create full-text search virtual table
            """
                CREATE VIRTUAL TABLE IF NOT EXISTS emails_fts USING fts5(
                    subject,
                    body_text,
                    sender,
                    recipients,
                    content='emails',
                    content_rowid='id'
                );
            """,

            # Create triggers to keep FTS table in sync
            """
                CREATE TRIGGER IF NOT EXISTS emails_fts_insert AFTER INSERT ON emails BEGIN
                    INSERT INTO emails_fts(rowid, subject, body_text, sender, recipients)
                    VALUES (new.id, new.subject, new.body_text, new.sender, new.recipients);
                END;
            """,
            """
                CREATE TRIGGER IF NOT EXISTS emails_fts_delete AFTER DELETE ON emails BEGIN
                    DELETE FROM emails_fts WHERE rowid = old.id;
                END;
            """,
            """
                CREATE TRIGGER IF NOT EXISTS emails_fts_update AFTER UPDATE ON emails BEGIN
                    DELETE FROM emails_fts WHERE rowid = old.id;
                    INSERT INTO emails_fts(rowid, subject, body_text, sender, recipients)
                    VALUES (new.id, new.subject, new.body_text, new.sender, new.recipients);
                END;
            """
        ]

    def down(self) -> List[str]:
        """
        Return SQL statements to rollback the initial schema.

        Returns:
            List of SQL statements
        """
        return [
            # Drop triggers first
            "DROP TRIGGER IF EXISTS emails_fts_insert;",
            "DROP TRIGGER IF EXISTS emails_fts_delete;",
            "DROP TRIGGER IF EXISTS emails_fts_update;",

            # Drop FTS table
            "DROP TABLE IF EXISTS emails_fts;",

            # Drop indexes
            "DROP INDEX IF EXISTS idx_email_tags_tag_id;",
            "DROP INDEX IF EXISTS idx_email_tags_email_id;",
            "DROP INDEX IF EXISTS idx_tags_name;",
            "DROP INDEX IF EXISTS idx_history_performed_at;",
            "DROP INDEX IF EXISTS idx_history_action_type;",
            "DROP INDEX IF EXISTS idx_history_email_id;",
            "DROP INDEX IF EXISTS idx_rules_is_active;",
            "DROP INDEX IF EXISTS idx_rules_rule_type;",
            "DROP INDEX IF EXISTS idx_classifications_importance_level;",
            "DROP INDEX IF EXISTS idx_classifications_urgency_level;",
            "DROP INDEX IF EXISTS idx_classifications_priority_score;",
            "DROP INDEX IF EXISTS idx_classifications_email_id;",
            "DROP INDEX IF EXISTS idx_attachments_content_hash;",
            "DROP INDEX IF EXISTS idx_attachments_email_id;",
            "DROP INDEX IF EXISTS idx_emails_has_attachments;",
            "DROP INDEX IF EXISTS idx_emails_received_at;",
            "DROP INDEX IF EXISTS idx_emails_sender;",
            "DROP INDEX IF EXISTS idx_emails_message_id;",

            # Drop tables in reverse order
            "DROP TABLE IF EXISTS email_tags;",
            "DROP TABLE IF EXISTS tags;",
            "DROP TABLE IF EXISTS history;",
            "DROP TABLE IF EXISTS rules;",
            "DROP TABLE IF EXISTS classifications;",
            "DROP TABLE IF EXISTS attachments;",
            "DROP TABLE IF EXISTS emails;",
            "DROP TABLE IF EXISTS schema_version;"
        ]

    def check_prerequisites(self, db_manager) -> bool:
        """
        Check if prerequisites for this migration are met.

        Args:
            db_manager: Database connection manager

        Returns:
            True if prerequisites are met
        """
        # For initial schema, no prerequisites needed
        return True

    def post_apply(self, db_manager) -> None:
        """
        Perform post-migration operations.

        Args:
            db_manager: Database connection manager
        """
        # Insert default tags
        default_tags = [
            ('Important', 'Important emails that need attention', '#FF6B6B'),
            ('Work', 'Work-related emails', '#4ECDC4'),
            ('Personal', 'Personal emails', '#45B7D1'),
            ('Archive', 'Archived emails', '#96CEB4'),
            ('Spam', 'Spam or unwanted emails', '#DDA0DD')
        ]

        try:
            with db_manager.get_cursor() as cursor:
                for name, description, color in default_tags:
                    cursor.execute(
                        """
                            INSERT OR IGNORE INTO tags (name, description, color)
                            VALUES (?, ?, ?)
                        """,
                        (name, description, color)
                    )
        except Exception as e:
            # Log error but don't fail the migration
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to create default tags: {e}")

        # Insert default rules
        default_rules = [
            ('High Priority Senders', 'Mark emails from important senders as high priority', 'sender', 'boss@company.com', 'classify', 10),
            ('Urgent Keywords', 'Mark emails with urgent keywords as critical', 'keyword', 'urgent|asap|emergency', 'classify', 9),
            ('Large Attachments', 'Flag emails with large attachments', 'custom', 'size_bytes > 10000000', 'flag', 5)
        ]

        try:
            with db_manager.get_cursor() as cursor:
                for name, description, rule_type, condition, action, priority in default_rules:
                    cursor.execute(
                        """
                            INSERT OR IGNORE INTO rules (name, description, rule_type, condition, action, priority)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (name, description, rule_type, condition, action, priority)
                    )
        except Exception as e:
            # Log error but don't fail the migration
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to create default rules: {e}")