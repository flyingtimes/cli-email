"""
Database operations for email priority manager.
Provides CRUD operations for all entities.
"""

import sqlite3
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from .models import (
    Email, Attachment, Classification, Rule, History, Tag, EmailTag,
    create_email_from_row, create_attachment_from_row, create_classification_from_row,
    create_rule_from_row, create_history_from_row, create_tag_from_row, create_email_tag_from_row
)
from .connection import get_db_manager, DatabaseQueryError

logger = logging.getLogger(__name__)


class EmailOperations:
    """Operations for email entities."""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager or get_db_manager()

    def create(self, email: Email) -> Email:
        """
        Create a new email record.

        Args:
            email: Email object to create

        Returns:
            Created email with ID assigned
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO emails (
                        message_id, subject, sender, recipients, cc, bcc,
                        body_text, body_html, received_at, sent_at, size_bytes,
                        has_attachments, is_read, is_flagged, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    email.message_id, email.subject, email.sender, email.recipients,
                    email.cc, email.bcc, email.body_text, email.body_html,
                    email.received_at, email.sent_at, email.size_bytes,
                    email.has_attachments, email.is_read, email.is_flagged,
                    email.created_at, email.updated_at
                ))

                email.id = cursor.lastrowid
                logger.info(f"Created email with ID {email.id}")
                return email

        except sqlite3.IntegrityError as e:
            logger.error(f"Email with message_id {email.message_id} already exists: {e}")
            raise DatabaseQueryError(f"Email already exists: {e}")
        except sqlite3.Error as e:
            logger.error(f"Failed to create email: {e}")
            raise DatabaseQueryError(f"Failed to create email: {e}")

    def get_by_id(self, email_id: int) -> Optional[Email]:
        """
        Get email by ID.

        Args:
            email_id: Email ID

        Returns:
            Email object or None if not found
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM emails WHERE id = ?", (email_id,))
                row = cursor.fetchone()
                return create_email_from_row(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to get email {email_id}: {e}")
            raise DatabaseQueryError(f"Failed to get email: {e}")

    def get_by_message_id(self, message_id: str) -> Optional[Email]:
        """
        Get email by message ID.

        Args:
            message_id: Email message ID

        Returns:
            Email object or None if not found
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM emails WHERE message_id = ?", (message_id,))
                row = cursor.fetchone()
                return create_email_from_row(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to get email by message_id {message_id}: {e}")
            raise DatabaseQueryError(f"Failed to get email: {e}")

    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Email]:
        """
        Get all emails with pagination.

        Args:
            limit: Maximum number of emails to return
            offset: Offset for pagination

        Returns:
            List of email objects
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                query = "SELECT * FROM emails ORDER BY received_at DESC"
                params = []

                if limit:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                elif offset:
                    query += " OFFSET ?"
                    params.append(offset)

                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [create_email_from_row(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get emails: {e}")
            raise DatabaseQueryError(f"Failed to get emails: {e}")

    def update(self, email: Email) -> Email:
        """
        Update an email record.

        Args:
            email: Email object to update

        Returns:
            Updated email
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                email.updated_at = datetime.now()
                cursor.execute("""
                    UPDATE emails SET
                        subject = ?, sender = ?, recipients = ?, cc = ?, bcc = ?,
                        body_text = ?, body_html = ?, received_at = ?, sent_at = ?,
                        size_bytes = ?, has_attachments = ?, is_read = ?, is_flagged = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    email.subject, email.sender, email.recipients, email.cc, email.bcc,
                    email.body_text, email.body_html, email.received_at, email.sent_at,
                    email.size_bytes, email.has_attachments, email.is_read, email.is_flagged,
                    email.updated_at, email.id
                ))

                if cursor.rowcount == 0:
                    raise DatabaseQueryError(f"Email {email.id} not found")

                logger.info(f"Updated email {email.id}")
                return email

        except sqlite3.Error as e:
            logger.error(f"Failed to update email {email.id}: {e}")
            raise DatabaseQueryError(f"Failed to update email: {e}")

    def delete(self, email_id: int) -> bool:
        """
        Delete an email record.

        Args:
            email_id: Email ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("DELETE FROM emails WHERE id = ?", (email_id,))
                deleted = cursor.rowcount > 0

                if deleted:
                    logger.info(f"Deleted email {email_id}")

                return deleted

        except sqlite3.Error as e:
            logger.error(f"Failed to delete email {email_id}: {e}")
            raise DatabaseQueryError(f"Failed to delete email: {e}")

    def search(self, query: str, limit: Optional[int] = None) -> List[Email]:
        """
        Search emails using full-text search.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching email objects
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                sql = """
                    SELECT e.* FROM emails e
                    JOIN emails_fts fts ON e.id = fts.rowid
                    WHERE emails_fts MATCH ?
                    ORDER BY e.received_at DESC
                """
                params = [query]

                if limit:
                    sql += " LIMIT ?"
                    params.append(limit)

                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return [create_email_from_row(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to search emails: {e}")
            raise DatabaseQueryError(f"Failed to search emails: {e}")

    def count(self) -> int:
        """
        Get total email count.

        Returns:
            Total number of emails
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM emails")
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"Failed to count emails: {e}")
            raise DatabaseQueryError(f"Failed to count emails: {e}")


class AttachmentOperations:
    """Operations for attachment entities."""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager or get_db_manager()

    def create(self, attachment: Attachment) -> Attachment:
        """
        Create a new attachment record.

        Args:
            attachment: Attachment object to create

        Returns:
            Created attachment with ID assigned
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO attachments (
                        email_id, filename, file_path, size_bytes, mime_type, content_hash, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    attachment.email_id, attachment.filename, attachment.file_path,
                    attachment.size_bytes, attachment.mime_type, attachment.content_hash,
                    attachment.created_at
                ))

                attachment.id = cursor.lastrowid
                logger.info(f"Created attachment with ID {attachment.id}")
                return attachment

        except sqlite3.Error as e:
            logger.error(f"Failed to create attachment: {e}")
            raise DatabaseQueryError(f"Failed to create attachment: {e}")

    def get_by_id(self, attachment_id: int) -> Optional[Attachment]:
        """
        Get attachment by ID.

        Args:
            attachment_id: Attachment ID

        Returns:
            Attachment object or None if not found
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM attachments WHERE id = ?", (attachment_id,))
                row = cursor.fetchone()
                return create_attachment_from_row(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to get attachment {attachment_id}: {e}")
            raise DatabaseQueryError(f"Failed to get attachment: {e}")

    def get_by_email_id(self, email_id: int) -> List[Attachment]:
        """
        Get all attachments for an email.

        Args:
            email_id: Email ID

        Returns:
            List of attachment objects
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM attachments WHERE email_id = ?", (email_id,))
                rows = cursor.fetchall()
                return [create_attachment_from_row(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get attachments for email {email_id}: {e}")
            raise DatabaseQueryError(f"Failed to get attachments: {e}")

    def delete(self, attachment_id: int) -> bool:
        """
        Delete an attachment record.

        Args:
            attachment_id: Attachment ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("DELETE FROM attachments WHERE id = ?", (attachment_id,))
                deleted = cursor.rowcount > 0

                if deleted:
                    logger.info(f"Deleted attachment {attachment_id}")

                return deleted

        except sqlite3.Error as e:
            logger.error(f"Failed to delete attachment {attachment_id}: {e}")
            raise DatabaseQueryError(f"Failed to delete attachment: {e}")


class ClassificationOperations:
    """Operations for classification entities."""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager or get_db_manager()

    def create(self, classification: Classification) -> Classification:
        """
        Create a new classification record.

        Args:
            classification: Classification object to create

        Returns:
            Created classification with ID assigned
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO classifications (
                        email_id, priority_score, urgency_level, importance_level,
                        classification_type, confidence_score, ai_analysis,
                        classified_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    classification.email_id, classification.priority_score,
                    classification.urgency_level, classification.importance_level,
                    classification.classification_type, classification.confidence_score,
                    classification.ai_analysis, classification.classified_at,
                    classification.updated_at
                ))

                classification.id = cursor.lastrowid
                logger.info(f"Created classification with ID {classification.id}")
                return classification

        except sqlite3.IntegrityError as e:
            logger.error(f"Classification for email {classification.email_id} already exists: {e}")
            raise DatabaseQueryError(f"Classification already exists: {e}")
        except sqlite3.Error as e:
            logger.error(f"Failed to create classification: {e}")
            raise DatabaseQueryError(f"Failed to create classification: {e}")

    def get_by_id(self, classification_id: int) -> Optional[Classification]:
        """
        Get classification by ID.

        Args:
            classification_id: Classification ID

        Returns:
            Classification object or None if not found
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM classifications WHERE id = ?", (classification_id,))
                row = cursor.fetchone()
                return create_classification_from_row(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to get classification {classification_id}: {e}")
            raise DatabaseQueryError(f"Failed to get classification: {e}")

    def get_by_email_id(self, email_id: int) -> Optional[Classification]:
        """
        Get classification by email ID.

        Args:
            email_id: Email ID

        Returns:
            Classification object or None if not found
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM classifications WHERE email_id = ?", (email_id,))
                row = cursor.fetchone()
                return create_classification_from_row(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to get classification for email {email_id}: {e}")
            raise DatabaseQueryError(f"Failed to get classification: {e}")

    def update(self, classification: Classification) -> Classification:
        """
        Update a classification record.

        Args:
            classification: Classification object to update

        Returns:
            Updated classification
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                classification.updated_at = datetime.now()
                cursor.execute("""
                    UPDATE classifications SET
                        priority_score = ?, urgency_level = ?, importance_level = ?,
                        classification_type = ?, confidence_score = ?, ai_analysis = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    classification.priority_score, classification.urgency_level,
                    classification.importance_level, classification.classification_type,
                    classification.confidence_score, classification.ai_analysis,
                    classification.updated_at, classification.id
                ))

                if cursor.rowcount == 0:
                    raise DatabaseQueryError(f"Classification {classification.id} not found")

                logger.info(f"Updated classification {classification.id}")
                return classification

        except sqlite3.Error as e:
            logger.error(f"Failed to update classification {classification.id}: {e}")
            raise DatabaseQueryError(f"Failed to update classification: {e}")

    def get_by_priority(self, priority_score: int) -> List[Classification]:
        """
        Get classifications by priority score.

        Args:
            priority_score: Priority score to filter by

        Returns:
            List of classification objects
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM classifications WHERE priority_score = ?", (priority_score,))
                rows = cursor.fetchall()
                return [create_classification_from_row(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get classifications by priority {priority_score}: {e}")
            raise DatabaseQueryError(f"Failed to get classifications: {e}")

    def get_by_urgency(self, urgency_level: str) -> List[Classification]:
        """
        Get classifications by urgency level.

        Args:
            urgency_level: Urgency level to filter by

        Returns:
            List of classification objects
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM classifications WHERE urgency_level = ?", (urgency_level,))
                rows = cursor.fetchall()
                return [create_classification_from_row(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get classifications by urgency {urgency_level}: {e}")
            raise DatabaseQueryError(f"Failed to get classifications: {e}")


class RuleOperations:
    """Operations for rule entities."""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager or get_db_manager()

    def create(self, rule: Rule) -> Rule:
        """
        Create a new rule record.

        Args:
            rule: Rule object to create

        Returns:
            Created rule with ID assigned
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO rules (
                        name, description, rule_type, condition, action, priority, is_active,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule.name, rule.description, rule.rule_type, rule.condition,
                    rule.action, rule.priority, rule.is_active,
                    rule.created_at, rule.updated_at
                ))

                rule.id = cursor.lastrowid
                logger.info(f"Created rule with ID {rule.id}")
                return rule

        except sqlite3.Error as e:
            logger.error(f"Failed to create rule: {e}")
            raise DatabaseQueryError(f"Failed to create rule: {e}")

    def get_by_id(self, rule_id: int) -> Optional[Rule]:
        """
        Get rule by ID.

        Args:
            rule_id: Rule ID

        Returns:
            Rule object or None if not found
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM rules WHERE id = ?", (rule_id,))
                row = cursor.fetchone()
                return create_rule_from_row(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to get rule {rule_id}: {e}")
            raise DatabaseQueryError(f"Failed to get rule: {e}")

    def get_all(self, active_only: bool = False) -> List[Rule]:
        """
        Get all rules.

        Args:
            active_only: Only return active rules

        Returns:
            List of rule objects
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                query = "SELECT * FROM rules"
                params = []

                if active_only:
                    query += " WHERE is_active = ?"
                    params.append(True)

                query += " ORDER BY priority DESC, created_at ASC"

                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [create_rule_from_row(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get rules: {e}")
            raise DatabaseQueryError(f"Failed to get rules: {e}")

    def update(self, rule: Rule) -> Rule:
        """
        Update a rule record.

        Args:
            rule: Rule object to update

        Returns:
            Updated rule
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                rule.updated_at = datetime.now()
                cursor.execute("""
                    UPDATE rules SET
                        name = ?, description = ?, rule_type = ?, condition = ?,
                        action = ?, priority = ?, is_active = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    rule.name, rule.description, rule.rule_type, rule.condition,
                    rule.action, rule.priority, rule.is_active, rule.updated_at, rule.id
                ))

                if cursor.rowcount == 0:
                    raise DatabaseQueryError(f"Rule {rule.id} not found")

                logger.info(f"Updated rule {rule.id}")
                return rule

        except sqlite3.Error as e:
            logger.error(f"Failed to update rule {rule.id}: {e}")
            raise DatabaseQueryError(f"Failed to update rule: {e}")

    def delete(self, rule_id: int) -> bool:
        """
        Delete a rule record.

        Args:
            rule_id: Rule ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
                deleted = cursor.rowcount > 0

                if deleted:
                    logger.info(f"Deleted rule {rule_id}")

                return deleted

        except sqlite3.Error as e:
            logger.error(f"Failed to delete rule {rule_id}: {e}")
            raise DatabaseQueryError(f"Failed to delete rule: {e}")


class HistoryOperations:
    """Operations for history entities."""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager or get_db_manager()

    def create(self, history: History) -> History:
        """
        Create a new history record.

        Args:
            history: History object to create

        Returns:
            Created history with ID assigned
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO history (email_id, action_type, action_details, performed_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    history.email_id, history.action_type, history.action_details, history.performed_at
                ))

                history.id = cursor.lastrowid
                logger.info(f"Created history entry with ID {history.id}")
                return history

        except sqlite3.Error as e:
            logger.error(f"Failed to create history entry: {e}")
            raise DatabaseQueryError(f"Failed to create history entry: {e}")

    def get_by_email_id(self, email_id: int) -> List[History]:
        """
        Get history entries for an email.

        Args:
            email_id: Email ID

        Returns:
            List of history objects
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM history WHERE email_id = ? ORDER BY performed_at DESC
                """, (email_id,))
                rows = cursor.fetchall()
                return [create_history_from_row(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get history for email {email_id}: {e}")
            raise DatabaseQueryError(f"Failed to get history: {e}")

    def get_recent(self, limit: int = 50) -> List[History]:
        """
        Get recent history entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of history objects
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM history ORDER BY performed_at DESC LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                return [create_history_from_row(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get recent history: {e}")
            raise DatabaseQueryError(f"Failed to get recent history: {e}")


class TagOperations:
    """Operations for tag entities."""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager or get_db_manager()

    def create(self, tag: Tag) -> Tag:
        """
        Create a new tag record.

        Args:
            tag: Tag object to create

        Returns:
            Created tag with ID assigned
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tags (name, description, color, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    tag.name, tag.description, tag.color, tag.created_at
                ))

                tag.id = cursor.lastrowid
                logger.info(f"Created tag with ID {tag.id}")
                return tag

        except sqlite3.IntegrityError as e:
            logger.error(f"Tag with name {tag.name} already exists: {e}")
            raise DatabaseQueryError(f"Tag already exists: {e}")
        except sqlite3.Error as e:
            logger.error(f"Failed to create tag: {e}")
            raise DatabaseQueryError(f"Failed to create tag: {e}")

    def get_by_id(self, tag_id: int) -> Optional[Tag]:
        """
        Get tag by ID.

        Args:
            tag_id: Tag ID

        Returns:
            Tag object or None if not found
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM tags WHERE id = ?", (tag_id,))
                row = cursor.fetchone()
                return create_tag_from_row(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to get tag {tag_id}: {e}")
            raise DatabaseQueryError(f"Failed to get tag: {e}")

    def get_by_name(self, name: str) -> Optional[Tag]:
        """
        Get tag by name.

        Args:
            name: Tag name

        Returns:
            Tag object or None if not found
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM tags WHERE name = ?", (name,))
                row = cursor.fetchone()
                return create_tag_from_row(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to get tag by name {name}: {e}")
            raise DatabaseQueryError(f"Failed to get tag: {e}")

    def get_all(self) -> List[Tag]:
        """
        Get all tags.

        Returns:
            List of tag objects
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM tags ORDER BY name")
                rows = cursor.fetchall()
                return [create_tag_from_row(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get tags: {e}")
            raise DatabaseQueryError(f"Failed to get tags: {e}")

    def update(self, tag: Tag) -> Tag:
        """
        Update a tag record.

        Args:
            tag: Tag object to update

        Returns:
            Updated tag
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE tags SET name = ?, description = ?, color = ?
                    WHERE id = ?
                """, (tag.name, tag.description, tag.color, tag.id))

                if cursor.rowcount == 0:
                    raise DatabaseQueryError(f"Tag {tag.id} not found")

                logger.info(f"Updated tag {tag.id}")
                return tag

        except sqlite3.Error as e:
            logger.error(f"Failed to update tag {tag.id}: {e}")
            raise DatabaseQueryError(f"Failed to update tag: {e}")

    def delete(self, tag_id: int) -> bool:
        """
        Delete a tag record.

        Args:
            tag_id: Tag ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
                deleted = cursor.rowcount > 0

                if deleted:
                    logger.info(f"Deleted tag {tag_id}")

                return deleted

        except sqlite3.Error as e:
            logger.error(f"Failed to delete tag {tag_id}: {e}")
            raise DatabaseQueryError(f"Failed to delete tag: {e}")


class EmailTagOperations:
    """Operations for email-tag relationships."""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager or get_db_manager()

    def create(self, email_tag: EmailTag) -> EmailTag:
        """
        Create a new email-tag relationship.

        Args:
            email_tag: EmailTag object to create

        Returns:
            Created EmailTag
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT OR IGNORE INTO email_tags (email_id, tag_id, assigned_at)
                    VALUES (?, ?, ?)
                """, (
                    email_tag.email_id, email_tag.tag_id, email_tag.assigned_at
                ))

                logger.info(f"Created email-tag relationship for email {email_tag.email_id}, tag {email_tag.tag_id}")
                return email_tag

        except sqlite3.Error as e:
            logger.error(f"Failed to create email-tag relationship: {e}")
            raise DatabaseQueryError(f"Failed to create email-tag relationship: {e}")

    def get_email_tags(self, email_id: int) -> List[Tag]:
        """
        Get all tags for an email.

        Args:
            email_id: Email ID

        Returns:
            List of tag objects
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT t.* FROM tags t
                    JOIN email_tags et ON t.id = et.tag_id
                    WHERE et.email_id = ?
                    ORDER BY t.name
                """, (email_id,))
                rows = cursor.fetchall()
                return [create_tag_from_row(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get tags for email {email_id}: {e}")
            raise DatabaseQueryError(f"Failed to get email tags: {e}")

    def get_tag_emails(self, tag_id: int) -> List[Email]:
        """
        Get all emails with a specific tag.

        Args:
            tag_id: Tag ID

        Returns:
            List of email objects
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT e.* FROM emails e
                    JOIN email_tags et ON e.id = et.email_id
                    WHERE et.tag_id = ?
                    ORDER BY e.received_at DESC
                """, (tag_id,))
                rows = cursor.fetchall()
                return [create_email_from_row(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get emails for tag {tag_id}: {e}")
            raise DatabaseQueryError(f"Failed to get tag emails: {e}")

    def delete(self, email_id: int, tag_id: int) -> bool:
        """
        Delete an email-tag relationship.

        Args:
            email_id: Email ID
            tag_id: Tag ID

        Returns:
            True if deleted, False if not found
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM email_tags WHERE email_id = ? AND tag_id = ?
                """, (email_id, tag_id))
                deleted = cursor.rowcount > 0

                if deleted:
                    logger.info(f"Deleted email-tag relationship for email {email_id}, tag {tag_id}")

                return deleted

        except sqlite3.Error as e:
            logger.error(f"Failed to delete email-tag relationship: {e}")
            raise DatabaseQueryError(f"Failed to delete email-tag relationship: {e}")


# Database operations container
class DatabaseOperations:
    """Container for all database operations."""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager or get_db_manager()
        self.emails = EmailOperations(self.db_manager)
        self.attachments = AttachmentOperations(self.db_manager)
        self.classifications = ClassificationOperations(self.db_manager)
        self.rules = RuleOperations(self.db_manager)
        self.history = HistoryOperations(self.db_manager)
        self.tags = TagOperations(self.db_manager)
        self.email_tags = EmailTagOperations(self.db_manager)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with database statistics
        """
        try:
            stats = {}
            with self.db_manager.get_cursor() as cursor:

                # Email statistics
                cursor.execute("SELECT COUNT(*) FROM emails")
                stats['total_emails'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM emails WHERE has_attachments = 1")
                stats['emails_with_attachments'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM emails WHERE is_read = 0")
                stats['unread_emails'] = cursor.fetchone()[0]

                # Attachment statistics
                cursor.execute("SELECT COUNT(*) FROM attachments")
                stats['total_attachments'] = cursor.fetchone()[0]

                cursor.execute("SELECT SUM(size_bytes) FROM attachments")
                result = cursor.fetchone()[0]
                stats['total_attachment_size'] = result if result else 0

                # Classification statistics
                cursor.execute("SELECT COUNT(*) FROM classifications")
                stats['classified_emails'] = cursor.fetchone()[0]

                cursor.execute("SELECT AVG(priority_score) FROM classifications")
                result = cursor.fetchone()[0]
                stats['average_priority'] = round(result, 2) if result else 0

                cursor.execute("SELECT urgency_level, COUNT(*) FROM classifications GROUP BY urgency_level")
                stats['urgency_distribution'] = dict(cursor.fetchall())

                cursor.execute("SELECT importance_level, COUNT(*) FROM classifications GROUP BY importance_level")
                stats['importance_distribution'] = dict(cursor.fetchall())

                # Rule statistics
                cursor.execute("SELECT COUNT(*) FROM rules WHERE is_active = 1")
                stats['active_rules'] = cursor.fetchone()[0]

                # Tag statistics
                cursor.execute("SELECT COUNT(*) FROM tags")
                stats['total_tags'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM email_tags")
                stats['total_tag_assignments'] = cursor.fetchone()[0]

                # History statistics
                cursor.execute("SELECT COUNT(*) FROM history")
                stats['total_history_entries'] = cursor.fetchone()[0]

                # Database size
                stats['database_size'] = self.db_manager.get_database_size()

                return stats

        except sqlite3.Error as e:
            logger.error(f"Failed to get database statistics: {e}")
            raise DatabaseQueryError(f"Failed to get statistics: {e}")


# Convenience functions for getting operations
def get_email_operations(db_manager=None) -> EmailOperations:
    """Get email operations instance."""
    return EmailOperations(db_manager)


def get_attachment_operations(db_manager=None) -> AttachmentOperations:
    """Get attachment operations instance."""
    return AttachmentOperations(db_manager)


def get_classification_operations(db_manager=None) -> ClassificationOperations:
    """Get classification operations instance."""
    return ClassificationOperations(db_manager)


def get_rule_operations(db_manager=None) -> RuleOperations:
    """Get rule operations instance."""
    return RuleOperations(db_manager)


def get_history_operations(db_manager=None) -> HistoryOperations:
    """Get history operations instance."""
    return HistoryOperations(db_manager)


def get_tag_operations(db_manager=None) -> TagOperations:
    """Get tag operations instance."""
    return TagOperations(db_manager)


def get_email_tag_operations(db_manager=None) -> EmailTagOperations:
    """Get email-tag operations instance."""
    return EmailTagOperations(db_manager)


def get_database_operations(db_manager=None) -> DatabaseOperations:
    """Get database operations container."""
    return DatabaseOperations(db_manager)