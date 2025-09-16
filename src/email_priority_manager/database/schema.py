"""
Database schema definitions for email priority manager.
Defines all core tables and their relationships.
"""

SCHEMA_VERSION = 1

# SQL schema definitions
CREATE_TABLES_SQL = {
    'emails': """
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

    'attachments': """
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

    'classifications': """
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

    'rules': """
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

    'history': """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER,
            action_type TEXT NOT NULL,
            action_details TEXT,
            performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE SET NULL
        );
    """,

    'tags': """
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            color TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """,

    'email_tags': """
        CREATE TABLE IF NOT EXISTS email_tags (
            email_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (email_id, tag_id),
            FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        );
    """
}

# Index definitions for performance optimization
CREATE_INDEXES_SQL = {
    'emails_message_id': """
        CREATE INDEX IF NOT EXISTS idx_emails_message_id ON emails(message_id);
    """,

    'emails_sender': """
        CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender);
    """,

    'emails_received_at': """
        CREATE INDEX IF NOT EXISTS idx_emails_received_at ON emails(received_at);
    """,

    'emails_has_attachments': """
        CREATE INDEX IF NOT EXISTS idx_emails_has_attachments ON emails(has_attachments);
    """,

    'attachments_email_id': """
        CREATE INDEX IF NOT EXISTS idx_attachments_email_id ON attachments(email_id);
    """,

    'attachments_content_hash': """
        CREATE INDEX IF NOT EXISTS idx_attachments_content_hash ON attachments(content_hash);
    """,

    'classifications_email_id': """
        CREATE INDEX IF NOT EXISTS idx_classifications_email_id ON classifications(email_id);
    """,

    'classifications_priority_score': """
        CREATE INDEX IF NOT EXISTS idx_classifications_priority_score ON classifications(priority_score);
    """,

    'classifications_urgency_level': """
        CREATE INDEX IF NOT EXISTS idx_classifications_urgency_level ON classifications(urgency_level);
    """,

    'classifications_importance_level': """
        CREATE INDEX IF NOT EXISTS idx_classifications_importance_level ON classifications(importance_level);
    """,

    'rules_rule_type': """
        CREATE INDEX IF NOT EXISTS idx_rules_rule_type ON rules(rule_type);
    """,

    'rules_is_active': """
        CREATE INDEX IF NOT EXISTS idx_rules_is_active ON rules(is_active);
    """,

    'history_email_id': """
        CREATE INDEX IF NOT EXISTS idx_history_email_id ON history(email_id);
    """,

    'history_action_type': """
        CREATE INDEX IF NOT EXISTS idx_history_action_type ON history(action_type);
    """,

    'history_performed_at': """
        CREATE INDEX IF NOT EXISTS idx_history_performed_at ON history(performed_at);
    """,

    'tags_name': """
        CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);
    """,

    'email_tags_email_id': """
        CREATE INDEX IF NOT EXISTS idx_email_tags_email_id ON email_tags(email_id);
    """,

    'email_tags_tag_id': """
        CREATE INDEX IF NOT EXISTS idx_email_tags_tag_id ON email_tags(tag_id);
    """
}

# Full-text search virtual tables
CREATE_FTS_TABLES_SQL = {
    'emails_fts': """
        CREATE VIRTUAL TABLE IF NOT EXISTS emails_fts USING fts5(
            subject,
            body_text,
            sender,
            recipients,
            content='emails',
            content_rowid='id'
        );
    """,

    'emails_fts_triggers': """
        -- Trigger to keep FTS table in sync
        CREATE TRIGGER IF NOT EXISTS emails_fts_insert AFTER INSERT ON emails BEGIN
            INSERT INTO emails_fts(rowid, subject, body_text, sender, recipients)
            VALUES (new.id, new.subject, new.body_text, new.sender, new.recipients);
        END;

        CREATE TRIGGER IF NOT EXISTS emails_fts_delete AFTER DELETE ON emails BEGIN
            DELETE FROM emails_fts WHERE rowid = old.id;
        END;

        CREATE TRIGGER IF NOT EXISTS emails_fts_update AFTER UPDATE ON emails BEGIN
            DELETE FROM emails_fts WHERE rowid = old.id;
            INSERT INTO emails_fts(rowid, subject, body_text, sender, recipients)
            VALUES (new.id, new.subject, new.body_text, new.sender, new.recipients);
        END;
    """
}

# Version tracking table
CREATE_VERSION_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        description TEXT
    );
"""

# Get all SQL statements in execution order
def get_all_create_statements():
    """Return all SQL statements in the correct execution order."""
    statements = []

    # Add version table first
    statements.append(('schema_version', CREATE_VERSION_TABLE_SQL))

    # Add core tables
    for table_name, sql in CREATE_TABLES_SQL.items():
        statements.append((table_name, sql))

    # Add indexes
    for index_name, sql in CREATE_INDEXES_SQL.items():
        statements.append((index_name, sql))

    # Add FTS tables
    for fts_name, sql in CREATE_FTS_TABLES_SQL.items():
        statements.append((fts_name, sql))

    return statements

# Drop all tables (for testing/development)
def get_drop_statements():
    """Return DROP statements for all tables in reverse order."""
    drop_statements = [
        ('emails_fts_triggers', """
            DROP TRIGGER IF EXISTS emails_fts_insert;
            DROP TRIGGER IF EXISTS emails_fts_delete;
            DROP TRIGGER IF EXISTS emails_fts_update;
        """),
        ('emails_fts', "DROP TABLE IF EXISTS emails_fts;"),
        ('email_tags', "DROP TABLE IF EXISTS email_tags;"),
        ('tags', "DROP TABLE IF EXISTS tags;"),
        ('history', "DROP TABLE IF EXISTS history;"),
        ('rules', "DROP TABLE IF EXISTS rules;"),
        ('classifications', "DROP TABLE IF EXISTS classifications;"),
        ('attachments', "DROP TABLE IF EXISTS attachments;"),
        ('emails', "DROP TABLE IF EXISTS emails;"),
        ('schema_version', "DROP TABLE IF EXISTS schema_version;")
    ]

    # Drop indexes
    for index_name in CREATE_INDEXES_SQL.keys():
        drop_statements.append((index_name, f"DROP INDEX IF EXISTS {index_name};"))

    return drop_statements