"""
Database index management for performance optimization.
"""

import sqlite3
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class IndexType(Enum):
    """Types of database indexes."""
    BTREE = "BTREE"
    HASH = "HASH"
    FTS = "FTS"


@dataclass
class IndexInfo:
    """Index information structure."""
    name: str
    table: str
    columns: List[str]
    index_type: IndexType
    unique: bool = False
    where_clause: Optional[str] = None
    is_partial: bool = False


class DatabaseIndexManager:
    """Manages database indexes for performance optimization."""

    def __init__(self, db_path: str = "email_priority.db"):
        self.db_path = db_path

    def get_performance_indexes(self) -> List[IndexInfo]:
        """Get all performance-optimized indexes for the database."""
        return [
            # Email table indexes
            IndexInfo(
                name="idx_emails_message_id",
                table="emails",
                columns=["message_id"],
                index_type=IndexType.BTREE,
                unique=True
            ),
            IndexInfo(
                name="idx_emails_sender_received",
                table="emails",
                columns=["sender", "received_at"],
                index_type=IndexType.BTREE
            ),
            IndexInfo(
                name="idx_emails_received_at",
                table="emails",
                columns=["received_at"],
                index_type=IndexType.BTREE
            ),
            IndexInfo(
                name="idx_emails_priority_flags",
                table="emails",
                columns=["has_attachments", "is_flagged", "is_read"],
                index_type=IndexType.BTREE
            ),
            IndexInfo(
                name="idx_emails_size_received",
                table="emails",
                columns=["size_bytes", "received_at"],
                index_type=IndexType.BTREE,
                where_clause="size_bytes IS NOT NULL"
            ),

            # Classification table indexes
            IndexInfo(
                name="idx_classifications_email_id",
                table="classifications",
                columns=["email_id"],
                index_type=IndexType.BTREE,
                unique=True
            ),
            IndexInfo(
                name="idx_classifications_priority_urgency",
                table="classifications",
                columns=["priority_score", "urgency_level"],
                index_type=IndexType.BTREE
            ),
            IndexInfo(
                name="idx_classifications_urgency_importance",
                table="classifications",
                columns=["urgency_level", "importance_level"],
                index_type=IndexType.BTREE
            ),
            IndexInfo(
                name="idx_classifications_confidence",
                table="classifications",
                columns=["confidence_score"],
                index_type=IndexType.BTREE,
                where_clause="confidence_score IS NOT NULL"
            ),

            # Attachment table indexes
            IndexInfo(
                name="idx_attachments_email_id",
                table="attachments",
                columns=["email_id"],
                index_type=IndexType.BTREE
            ),
            IndexInfo(
                name="idx_attachments_filename",
                table="attachments",
                columns=["filename"],
                index_type=IndexType.BTREE
            ),
            IndexInfo(
                name="idx_attachments_mime_type",
                table="attachments",
                columns=["mime_type"],
                index_type=IndexType.BTREE,
                where_clause="mime_type IS NOT NULL"
            ),
            IndexInfo(
                name="idx_attachments_size",
                table="attachments",
                columns=["size_bytes"],
                index_type=IndexType.BTREE,
                where_clause="size_bytes IS NOT NULL"
            ),

            # Rules table indexes
            IndexInfo(
                name="idx_rules_active_priority",
                table="rules",
                columns=["is_active", "priority"],
                index_type=IndexType.BTREE,
                where_clause="is_active = 1"
            ),
            IndexInfo(
                name="idx_rules_type_active",
                table="rules",
                columns=["rule_type", "is_active"],
                index_type=IndexType.BTREE
            ),

            # History table indexes
            IndexInfo(
                name="idx_history_email_id_action",
                table="history",
                columns=["email_id", "action_type"],
                index_type=IndexType.BTREE
            ),
            IndexInfo(
                name="idx_history_action_performed",
                table="history",
                columns=["action_type", "performed_at"],
                index_type=IndexType.BTREE
            ),
            IndexInfo(
                name="idx_history_performed_at",
                table="history",
                columns=["performed_at"],
                index_type=IndexType.BTREE
            ),

            # Tags table indexes
            IndexInfo(
                name="idx_tags_name",
                table="tags",
                columns=["name"],
                index_type=IndexType.BTREE,
                unique=True
            ),

            # Email_tags junction table indexes
            IndexInfo(
                name="idx_email_tags_tag_id",
                table="email_tags",
                columns=["tag_id"],
                index_type=IndexType.BTREE
            ),
            IndexInfo(
                name="idx_email_tags_assigned_at",
                table="email_tags",
                columns=["assigned_at"],
                index_type=IndexType.BTREE
            ),
        ]

    def create_all_indexes(self) -> None:
        """Create all performance indexes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for index_info in self.get_performance_indexes():
                self._create_index(cursor, index_info)

            conn.commit()

    def create_index(self, index_info: IndexInfo) -> None:
        """Create a single index."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            self._create_index(cursor, index_info)
            conn.commit()

    def _create_index(self, cursor: sqlite3.Cursor, index_info: IndexInfo) -> None:
        """Create an index using the cursor."""
        columns_str = ", ".join(index_info.columns)

        sql = f"CREATE "
        if index_info.unique:
            sql += "UNIQUE "
        sql += f"INDEX IF NOT EXISTS {index_info.name} ON {index_info.table} ({columns_str})"

        if index_info.where_clause:
            sql += f" WHERE {index_info.where_clause}"

        cursor.execute(sql)

    def drop_index(self, index_name: str) -> None:
        """Drop an index."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
            conn.commit()

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about database indexes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get all indexes
            cursor.execute("""
                SELECT
                    name,
                    tbl_name as table_name,
                    sql
                FROM sqlite_master
                WHERE type='index'
                AND name NOT LIKE 'sqlite_%'
                ORDER BY tbl_name, name
            """)
            indexes = cursor.fetchall()

            # Get index usage statistics (SQLite specific)
            cursor.execute("PRAGMA index_list('emails')")
            email_indexes = cursor.fetchall()

            cursor.execute("PRAGMA index_list('classifications')")
            classification_indexes = cursor.fetchall()

            return {
                "total_indexes": len(indexes),
                "indexes": [
                    {
                        "name": row[0],
                        "table": row[1],
                        "sql": row[2]
                    }
                    for row in indexes
                ],
                "table_stats": {
                    "emails": len(email_indexes),
                    "classifications": len(classification_indexes)
                }
            }

    def analyze_indexes(self) -> Dict[str, Any]:
        """Analyze index usage and provide recommendations."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get table statistics
            tables = ["emails", "classifications", "attachments", "rules", "history", "tags", "email_tags"]
            table_stats = {}

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_stats[table] = count

            # Get index information
            cursor.execute("""
                SELECT
                    tbl_name,
                    COUNT(*) as index_count
                FROM sqlite_master
                WHERE type='index'
                AND name NOT LIKE 'sqlite_%'
                GROUP BY tbl_name
            """)
            index_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Analyze and provide recommendations
            recommendations = []

            # Check for tables without indexes
            for table, count in table_stats.items():
                if count > 100 and index_counts.get(table, 0) == 0:
                    recommendations.append({
                        "type": "missing_indexes",
                        "table": table,
                        "message": f"Table '{table}' has {count} rows but no indexes",
                        "priority": "high"
                    })

            # Check for over-indexing
            for table, idx_count in index_counts.items():
                if idx_count > 5 and table_stats.get(table, 0) < 1000:
                    recommendations.append({
                        "type": "over_indexed",
                        "table": table,
                        "message": f"Table '{table}' has {idx_count} indexes but only {table_stats.get(table, 0)} rows",
                        "priority": "medium"
                    })

            return {
                "table_stats": table_stats,
                "index_counts": index_counts,
                "recommendations": recommendations,
                "analysis_time": time.time()
            }

    def optimize_indexes(self) -> None:
        """Optimize indexes by rebuilding and analyzing."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Analyze the database for query optimization
            cursor.execute("ANALYZE")

            # Rebuild indexes if needed
            cursor.execute("PRAGMA optimize")

            conn.commit()

    def create_compound_indexes_for_common_queries(self) -> None:
        """Create compound indexes for common query patterns."""
        compound_indexes = [
            # Common priority-based queries
            IndexInfo(
                name="idx_email_priority_query",
                table="emails",
                columns=["received_at", "has_attachments", "is_flagged"],
                index_type=IndexType.BTREE
            ),

            # Common classification queries
            IndexInfo(
                name="idx_classification_priority_date",
                table="classifications",
                columns=["priority_score", "classified_at"],
                index_type=IndexType.BTREE
            ),

            # Common sender-based queries
            IndexInfo(
                name="idx_sender_date_received",
                table="emails",
                columns=["sender", "received_at"],
                index_type=IndexType.BTREE
            ),

            # Common attachment queries
            IndexInfo(
                name="idx_attachment_email_mime",
                table="attachments",
                columns=["email_id", "mime_type"],
                index_type=IndexType.BTREE
            ),
        ]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for index_info in compound_indexes:
                self._create_index(cursor, index_info)

            conn.commit()

    def get_query_performance_hints(self) -> Dict[str, List[str]]:
        """Get performance hints for common query patterns."""
        return {
            "email_search": [
                "Use idx_emails_message_id for exact message ID lookups",
                "Use idx_emails_sender_received for sender-based searches with date range",
                "Use idx_emails_received_at for date-range queries",
                "Consider FTS for full-text search on subject and body"
            ],
            "priority_queries": [
                "Use idx_classifications_priority_urgency for priority-based filtering",
                "Use idx_classification_priority_date for priority sorting with time",
                "Combine with email indexes for complex queries"
            ],
            "attachment_queries": [
                "Use idx_attachments_email_id for attachment lookups by email",
                "Use idx_attachments_filename for filename searches",
                "Use idx_attachment_email_mime for mime-type filtering"
            ],
            "history_queries": [
                "Use idx_history_action_performed for action-based history searches",
                "Use idx_history_performed_at for time-based history queries"
            ]
        }

    def backup_indexes(self, backup_path: str) -> None:
        """Backup index definitions to a SQL file."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get all index definitions
            cursor.execute("""
                SELECT sql
                FROM sqlite_master
                WHERE type='index'
                AND name NOT LIKE 'sqlite_%'
                AND sql IS NOT NULL
            """)

            index_definitions = cursor.fetchall()

            # Write to backup file
            with open(backup_path, 'w') as f:
                f.write("-- Database Index Backup\n")
                f.write(f"-- Generated at: {time.time()}\n\n")

                for row in index_definitions:
                    if row[0]:
                        f.write(f"{row[0]};\n\n")

    def restore_indexes_from_backup(self, backup_path: str) -> None:
        """Restore indexes from a SQL backup file."""
        with open(backup_path, 'r') as f:
            sql_content = f.read()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Execute each index creation statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

            for statement in statements:
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                    except sqlite3.Error as e:
                        print(f"Warning: Could not restore index: {e}")

            conn.commit()