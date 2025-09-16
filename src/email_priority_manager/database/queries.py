"""
Complex query functions for email retrieval and analysis.
"""

import sqlite3
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum


class PriorityLevel(Enum):
    """Email priority levels."""
    LOW = 1
    MEDIUM = 2
    NORMAL = 3
    HIGH = 4
    CRITICAL = 5


class UrgencyLevel(Enum):
    """Email urgency levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EmailSummary:
    """Email summary data structure."""
    id: int
    message_id: str
    subject: str
    sender: str
    recipients: str
    received_at: str
    has_attachments: bool
    is_read: bool
    is_flagged: bool
    priority_score: int
    urgency_level: str
    importance_level: str
    confidence_score: float
    attachment_count: int
    tag_count: int


@dataclass
class EmailDetail:
    """Detailed email information."""
    id: int
    message_id: str
    subject: str
    sender: str
    recipients: str
    cc: Optional[str]
    bcc: Optional[str]
    body_text: Optional[str]
    body_html: Optional[str]
    received_at: str
    sent_at: Optional[str]
    size_bytes: Optional[int]
    has_attachments: bool
    is_read: bool
    is_flagged: bool
    created_at: str
    updated_at: str

    # Classification data
    priority_score: int
    urgency_level: str
    importance_level: str
    classification_type: str
    confidence_score: float
    ai_analysis: Optional[str]
    classified_at: str

    # Related data
    attachments: List[Dict[str, Any]]
    tags: List[Dict[str, Any]]
    history: List[Dict[str, Any]]


@dataclass
class QueryFilter:
    """Query filter for complex queries."""
    field: str
    operator: str
    value: Any
    logical_operator: str = "AND"


@dataclass
class QueryOptions:
    """Query options for pagination and sorting."""
    limit: int = 50
    offset: int = 0
    order_by: str = "received_at"
    order_direction: str = "DESC"
    include_count: bool = False


class EmailQueries:
    """Complex query functions for email retrieval."""

    def __init__(self, db_path: str = "email_priority.db"):
        self.db_path = db_path

    def get_emails_by_priority(
        self,
        min_priority: int = 1,
        max_priority: int = 5,
        options: Optional[QueryOptions] = None,
        filters: Optional[List[QueryFilter]] = None
    ) -> Tuple[List[EmailSummary], Optional[int]]:
        """
        Get emails filtered by priority score.

        Args:
            min_priority: Minimum priority score (1-5)
            max_priority: Maximum priority score (1-5)
            options: Query options for pagination and sorting
            filters: Additional filters to apply

        Returns:
            Tuple of (email list, total count if requested)
        """
        if options is None:
            options = QueryOptions()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Build main query
            query = """
                SELECT
                    e.id, e.message_id, e.subject, e.sender, e.recipients,
                    e.received_at, e.has_attachments, e.is_read, e.is_flagged,
                    c.priority_score, c.urgency_level, c.importance_level, c.confidence_score,
                    COUNT(a.id) as attachment_count,
                    COUNT(et.tag_id) as tag_count
                FROM emails e
                LEFT JOIN classifications c ON e.id = c.email_id
                LEFT JOIN attachments a ON e.id = a.email_id
                LEFT JOIN email_tags et ON e.id = et.email_id
                WHERE c.priority_score BETWEEN ? AND ?
            """

            params = [min_priority, max_priority]

            # Add filters
            if filters:
                for filter_obj in filters:
                    query += f" {filter_obj.logical_operator} e.{filter_obj.field} {filter_obj.operator} ?"
                    params.append(filter_obj.value)

            # Group by
            query += " GROUP BY e.id, e.message_id, e.subject, e.sender, e.recipients, e.received_at, e.has_attachments, e.is_read, e.is_flagged, c.priority_score, c.urgency_level, c.importance_level, c.confidence_score"

            # Order by
            query += f" ORDER BY {options.order_by} {options.order_direction}"

            # Limit and offset
            query += " LIMIT ? OFFSET ?"
            params.extend([options.limit, options.offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            emails = [self._row_to_email_summary(row) for row in rows]

            # Get total count if requested
            total_count = None
            if options.include_count:
                total_count = self._get_priority_email_count(min_priority, max_priority, filters)

            return emails, total_count

    def get_emails_by_urgency(
        self,
        urgency_levels: List[str],
        options: Optional[QueryOptions] = None,
        filters: Optional[List[QueryFilter]] = None
    ) -> Tuple[List[EmailSummary], Optional[int]]:
        """
        Get emails filtered by urgency levels.

        Args:
            urgency_levels: List of urgency levels to filter by
            options: Query options for pagination and sorting
            filters: Additional filters to apply

        Returns:
            Tuple of (email list, total count if requested)
        """
        if options is None:
            options = QueryOptions()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Build main query
            query = """
                SELECT
                    e.id, e.message_id, e.subject, e.sender, e.recipients,
                    e.received_at, e.has_attachments, e.is_read, e.is_flagged,
                    c.priority_score, c.urgency_level, c.importance_level, c.confidence_score,
                    COUNT(a.id) as attachment_count,
                    COUNT(et.tag_id) as tag_count
                FROM emails e
                LEFT JOIN classifications c ON e.id = c.email_id
                LEFT JOIN attachments a ON e.id = a.email_id
                LEFT JOIN email_tags et ON e.id = et.email_id
                WHERE c.urgency_level IN ({})
            """.format(','.join(['?' for _ in urgency_levels]))

            params = urgency_levels

            # Add filters
            if filters:
                for filter_obj in filters:
                    query += f" {filter_obj.logical_operator} e.{filter_obj.field} {filter_obj.operator} ?"
                    params.append(filter_obj.value)

            # Group by
            query += " GROUP BY e.id, e.message_id, e.subject, e.sender, e.recipients, e.received_at, e.has_attachments, e.is_read, e.is_flagged, c.priority_score, c.urgency_level, c.importance_level, c.confidence_score"

            # Order by
            query += f" ORDER BY {options.order_by} {options.order_direction}"

            # Limit and offset
            query += " LIMIT ? OFFSET ?"
            params.extend([options.limit, options.offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            emails = [self._row_to_email_summary(row) for row in rows]

            # Get total count if requested
            total_count = None
            if options.include_count:
                total_count = self._get_urgency_email_count(urgency_levels, filters)

            return emails, total_count

    def get_email_by_id(self, email_id: int) -> Optional[EmailDetail]:
        """
        Get detailed email information by ID.

        Args:
            email_id: Email ID to retrieve

        Returns:
            Detailed email information or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get email basic info
            cursor.execute("""
                SELECT e.*, c.*
                FROM emails e
                LEFT JOIN classifications c ON e.id = c.email_id
                WHERE e.id = ?
            """, (email_id,))

            email_row = cursor.fetchone()
            if not email_row:
                return None

            # Get attachments
            cursor.execute("""
                SELECT id, filename, file_path, size_bytes, mime_type, content_hash, created_at
                FROM attachments
                WHERE email_id = ?
                ORDER BY filename
            """, (email_id,))
            attachments = [dict(row) for row in cursor.fetchall()]

            # Get tags
            cursor.execute("""
                SELECT t.id, t.name, t.description, t.color, et.assigned_at
                FROM tags t
                JOIN email_tags et ON t.id = et.tag_id
                WHERE et.email_id = ?
                ORDER BY t.name
            """, (email_id,))
            tags = [dict(row) for row in cursor.fetchall()]

            # Get history
            cursor.execute("""
                SELECT id, action_type, action_details, performed_at
                FROM history
                WHERE email_id = ?
                ORDER BY performed_at DESC
            """, (email_id,))
            history = [dict(row) for row in cursor.fetchall()]

            return self._row_to_email_detail(email_row, attachments, tags, history)

    def get_emails_by_sender(
        self,
        sender: str,
        options: Optional[QueryOptions] = None,
        partial_match: bool = True
    ) -> Tuple[List[EmailSummary], Optional[int]]:
        """
        Get emails by sender.

        Args:
            sender: Sender email or name
            options: Query options for pagination and sorting
            partial_match: Whether to use partial matching (LIKE)

        Returns:
            Tuple of (email list, total count if requested)
        """
        if options is None:
            options = QueryOptions()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Build query
            if partial_match:
                where_clause = "WHERE e.sender LIKE ?"
                sender_param = f"%{sender}%"
            else:
                where_clause = "WHERE e.sender = ?"
                sender_param = sender

            query = f"""
                SELECT
                    e.id, e.message_id, e.subject, e.sender, e.recipients,
                    e.received_at, e.has_attachments, e.is_read, e.is_flagged,
                    c.priority_score, c.urgency_level, c.importance_level, c.confidence_score,
                    COUNT(a.id) as attachment_count,
                    COUNT(et.tag_id) as tag_count
                FROM emails e
                LEFT JOIN classifications c ON e.id = c.email_id
                LEFT JOIN attachments a ON e.id = a.email_id
                LEFT JOIN email_tags et ON e.id = et.email_id
                {where_clause}
                GROUP BY e.id, e.message_id, e.subject, e.sender, e.recipients, e.received_at, e.has_attachments, e.is_read, e.is_flagged, c.priority_score, c.urgency_level, c.importance_level, c.confidence_score
                ORDER BY {options.order_by} {options.order_direction}
                LIMIT ? OFFSET ?
            """

            params = [sender_param, options.limit, options.offset]
            cursor.execute(query, params)
            rows = cursor.fetchall()

            emails = [self._row_to_email_summary(row) for row in rows]

            # Get total count if requested
            total_count = None
            if options.include_count:
                total_count = self._get_sender_email_count(sender, partial_match)

            return emails, total_count

    def get_emails_by_date_range(
        self,
        start_date: str,
        end_date: str,
        options: Optional[QueryOptions] = None,
        filters: Optional[List[QueryFilter]] = None
    ) -> Tuple[List[EmailSummary], Optional[int]]:
        """
        Get emails within a date range.

        Args:
            start_date: Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
            end_date: End date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
            options: Query options for pagination and sorting
            filters: Additional filters to apply

        Returns:
            Tuple of (email list, total count if requested)
        """
        if options is None:
            options = QueryOptions()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Build query
            query = """
                SELECT
                    e.id, e.message_id, e.subject, e.sender, e.recipients,
                    e.received_at, e.has_attachments, e.is_read, e.is_flagged,
                    c.priority_score, c.urgency_level, c.importance_level, c.confidence_score,
                    COUNT(a.id) as attachment_count,
                    COUNT(et.tag_id) as tag_count
                FROM emails e
                LEFT JOIN classifications c ON e.id = c.email_id
                LEFT JOIN attachments a ON e.id = a.email_id
                LEFT JOIN email_tags et ON e.id = et.email_id
                WHERE e.received_at BETWEEN ? AND ?
            """

            params = [start_date, end_date]

            # Add filters
            if filters:
                for filter_obj in filters:
                    query += f" {filter_obj.logical_operator} e.{filter_obj.field} {filter_obj.operator} ?"
                    params.append(filter_obj.value)

            # Group by
            query += " GROUP BY e.id, e.message_id, e.subject, e.sender, e.recipients, e.received_at, e.has_attachments, e.is_read, e.is_flagged, c.priority_score, c.urgency_level, c.importance_level, c.confidence_score"

            # Order by
            query += f" ORDER BY {options.order_by} {options.order_direction}"

            # Limit and offset
            query += " LIMIT ? OFFSET ?"
            params.extend([options.limit, options.offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            emails = [self._row_to_email_summary(row) for row in rows]

            # Get total count if requested
            total_count = None
            if options.include_count:
                total_count = self._get_date_range_email_count(start_date, end_date, filters)

            return emails, total_count

    def get_email_statistics(self) -> Dict[str, Any]:
        """
        Get email statistics and analytics.

        Returns:
            Dictionary with email statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total emails
            cursor.execute("SELECT COUNT(*) FROM emails")
            total_emails = cursor.fetchone()[0]

            # Emails by priority
            cursor.execute("""
                SELECT priority_score, COUNT(*) as count
                FROM classifications
                GROUP BY priority_score
                ORDER BY priority_score
            """)
            priority_stats = {row[0]: row[1] for row in cursor.fetchall()}

            # Emails by urgency
            cursor.execute("""
                SELECT urgency_level, COUNT(*) as count
                FROM classifications
                GROUP BY urgency_level
            """)
            urgency_stats = {row[0]: row[1] for row in cursor.fetchall()}

            # Emails with attachments
            cursor.execute("SELECT COUNT(*) FROM emails WHERE has_attachments = 1")
            emails_with_attachments = cursor.fetchone()[0]

            # Unread emails
            cursor.execute("SELECT COUNT(*) FROM emails WHERE is_read = 0")
            unread_emails = cursor.fetchone()[0]

            # Flagged emails
            cursor.execute("SELECT COUNT(*) FROM emails WHERE is_flagged = 1")
            flagged_emails = cursor.fetchone()[0]

            # Recent emails (last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("SELECT COUNT(*) FROM emails WHERE received_at >= ?", (week_ago,))
            recent_emails = cursor.fetchone()[0]

            return {
                "total_emails": total_emails,
                "priority_distribution": priority_stats,
                "urgency_distribution": urgency_stats,
                "emails_with_attachments": emails_with_attachments,
                "unread_emails": unread_emails,
                "flagged_emails": flagged_emails,
                "recent_emails": recent_emails,
                "attachment_rate": (emails_with_attachments / total_emails * 100) if total_emails > 0 else 0,
                "unread_rate": (unread_emails / total_emails * 100) if total_emails > 0 else 0
            }

    def get_top_senders(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top senders by email count.

        Args:
            limit: Maximum number of senders to return

        Returns:
            List of sender statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    sender,
                    COUNT(*) as email_count,
                    MAX(received_at) as last_email_date
                FROM emails
                GROUP BY sender
                ORDER BY email_count DESC
                LIMIT ?
            """, (limit,))

            return [
                {
                    "sender": row[0],
                    "email_count": row[1],
                    "last_email_date": row[2]
                }
                for row in cursor.fetchall()
            ]

    def _row_to_email_summary(self, row: sqlite3.Row) -> EmailSummary:
        """Convert database row to EmailSummary."""
        return EmailSummary(
            id=row['id'],
            message_id=row['message_id'],
            subject=row['subject'],
            sender=row['sender'],
            recipients=row['recipients'],
            received_at=row['received_at'],
            has_attachments=bool(row['has_attachments']),
            is_read=bool(row['is_read']),
            is_flagged=bool(row['is_flagged']),
            priority_score=row['priority_score'] or 0,
            urgency_level=row['urgency_level'] or 'low',
            importance_level=row['importance_level'] or 'low',
            confidence_score=row['confidence_score'] or 0.0,
            attachment_count=row['attachment_count'] or 0,
            tag_count=row['tag_count'] or 0
        )

    def _row_to_email_detail(
        self,
        row: sqlite3.Row,
        attachments: List[Dict[str, Any]],
        tags: List[Dict[str, Any]],
        history: List[Dict[str, Any]]
    ) -> EmailDetail:
        """Convert database row to EmailDetail."""
        return EmailDetail(
            id=row['id'],
            message_id=row['message_id'],
            subject=row['subject'],
            sender=row['sender'],
            recipients=row['recipients'],
            cc=row['cc'],
            bcc=row['bcc'],
            body_text=row['body_text'],
            body_html=row['body_html'],
            received_at=row['received_at'],
            sent_at=row['sent_at'],
            size_bytes=row['size_bytes'],
            has_attachments=bool(row['has_attachments']),
            is_read=bool(row['is_read']),
            is_flagged=bool(row['is_flagged']),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            priority_score=row['priority_score'] or 0,
            urgency_level=row['urgency_level'] or 'low',
            importance_level=row['importance_level'] or 'low',
            classification_type=row['classification_type'] or '',
            confidence_score=row['confidence_score'] or 0.0,
            ai_analysis=row['ai_analysis'],
            classified_at=row['classified_at'],
            attachments=attachments,
            tags=tags,
            history=history
        )

    def _get_priority_email_count(
        self,
        min_priority: int,
        max_priority: int,
        filters: Optional[List[QueryFilter]] = None
    ) -> int:
        """Get count of emails by priority range."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = """
                SELECT COUNT(DISTINCT e.id)
                FROM emails e
                LEFT JOIN classifications c ON e.id = c.email_id
                WHERE c.priority_score BETWEEN ? AND ?
            """
            params = [min_priority, max_priority]

            if filters:
                for filter_obj in filters:
                    query += f" {filter_obj.logical_operator} e.{filter_obj.field} {filter_obj.operator} ?"
                    params.append(filter_obj.value)

            cursor.execute(query, params)
            return cursor.fetchone()[0]

    def _get_urgency_email_count(
        self,
        urgency_levels: List[str],
        filters: Optional[List[QueryFilter]] = None
    ) -> int:
        """Get count of emails by urgency levels."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = f"""
                SELECT COUNT(DISTINCT e.id)
                FROM emails e
                LEFT JOIN classifications c ON e.id = c.email_id
                WHERE c.urgency_level IN ({','.join(['?' for _ in urgency_levels])})
            """
            params = urgency_levels

            if filters:
                for filter_obj in filters:
                    query += f" {filter_obj.logical_operator} e.{filter_obj.field} {filter_obj.operator} ?"
                    params.append(filter_obj.value)

            cursor.execute(query, params)
            return cursor.fetchone()[0]

    def _get_sender_email_count(self, sender: str, partial_match: bool) -> int:
        """Get count of emails by sender."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if partial_match:
                query = "SELECT COUNT(*) FROM emails WHERE sender LIKE ?"
                sender_param = f"%{sender}%"
            else:
                query = "SELECT COUNT(*) FROM emails WHERE sender = ?"
                sender_param = sender

            cursor.execute(query, (sender_param,))
            return cursor.fetchone()[0]

    def _get_date_range_email_count(
        self,
        start_date: str,
        end_date: str,
        filters: Optional[List[QueryFilter]] = None
    ) -> int:
        """Get count of emails by date range."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = """
                SELECT COUNT(*)
                FROM emails e
                WHERE e.received_at BETWEEN ? AND ?
            """
            params = [start_date, end_date]

            if filters:
                for filter_obj in filters:
                    query += f" {filter_obj.logical_operator} e.{filter_obj.field} {filter_obj.operator} ?"
                    params.append(filter_obj.value)

            cursor.execute(query, params)
            return cursor.fetchone()[0]