"""
Database module for email priority manager.
Provides complete database functionality including schema, models, and operations.
"""

from .connection import (
    DatabaseConnectionManager,
    DatabaseConnectionError,
    DatabaseTransactionError,
    DatabaseQueryError,
    DatabaseOperationError,
    get_db_manager,
    get_connection,
    get_cursor,
    transaction,
    execute_query,
    execute_script,
    close_global_connection,
    set_database_path
)

from .models import (
    Email,
    Attachment,
    Classification,
    Rule,
    History,
    Tag,
    EmailTag
)

from .schema import (
    SCHEMA_VERSION,
    get_all_create_statements,
    get_drop_statements
)

from .migrations import (
    Migration,
    MigrationManager,
    MigrationError,
    get_migration_manager,
    migrate,
    rollback,
    create_database,
    reset_database,
    get_migration_status
)

from .operations import (
    EmailOperations,
    AttachmentOperations,
    ClassificationOperations,
    RuleOperations,
    HistoryOperations,
    TagOperations,
    EmailTagOperations,
    DatabaseOperations,
    get_email_operations,
    get_attachment_operations,
    get_classification_operations,
    get_rule_operations,
    get_history_operations,
    get_tag_operations,
    get_email_tag_operations,
    get_database_operations
)

__all__ = [
    # Connection management
    'DatabaseConnectionManager',
    'DatabaseConnectionError',
    'DatabaseTransactionError',
    'DatabaseQueryError',
    'DatabaseOperationError',
    'get_db_manager',
    'get_connection',
    'get_cursor',
    'transaction',
    'execute_query',
    'execute_script',
    'close_global_connection',
    'set_database_path',

    # Models
    'Email',
    'Attachment',
    'Classification',
    'Rule',
    'History',
    'Tag',
    'EmailTag',

    # Schema
    'SCHEMA_VERSION',
    'get_all_create_statements',
    'get_drop_statements',

    # Migrations
    'Migration',
    'MigrationManager',
    'MigrationError',
    'get_migration_manager',
    'migrate',
    'rollback',
    'create_database',
    'reset_database',
    'get_migration_status',

    # Operations
    'EmailOperations',
    'AttachmentOperations',
    'ClassificationOperations',
    'RuleOperations',
    'HistoryOperations',
    'TagOperations',
    'EmailTagOperations',
    'DatabaseOperations',
    'get_email_operations',
    'get_attachment_operations',
    'get_classification_operations',
    'get_rule_operations',
    'get_history_operations',
    'get_tag_operations',
    'get_email_tag_operations',
    'get_database_operations'
]