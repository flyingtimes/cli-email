"""
Full-text search implementation for the email priority manager.
"""

import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SearchScope(Enum):
    """Search scope for email fields."""
    ALL = "all"
    SUBJECT = "subject"
    SENDER = "sender"
    RECIPIENTS = "recipients"
    BODY = "body_text"


class SearchOperator(Enum):
    """Search operators for combining terms."""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


@dataclass
class SearchFilter:
    """Search filter configuration."""
    field: str
    operator: str
    value: Any


@dataclass
class SearchResult:
    """Search result data structure."""
    email_id: int
    message_id: str
    subject: str
    sender: str
    recipients: str
    body_text: Optional[str]
    received_at: str
    score: float
    snippet: Optional[str] = None


class EmailSearch:
    """Full-text search implementation for emails."""

    def __init__(self, db_path: str = "email_priority.db"):
        self.db_path = db_path

    def search(
        self,
        query: str,
        scope: SearchScope = SearchScope.ALL,
        filters: Optional[List[SearchFilter]] = None,
        limit: int = 50,
        offset: int = 0,
        operator: SearchOperator = SearchOperator.AND
    ) -> List[SearchResult]:
        """
        Perform full-text search on emails.

        Args:
            query: Search query string
            scope: Search scope (which fields to search)
            filters: Additional filters to apply
            limit: Maximum number of results
            offset: Offset for pagination
            operator: Search operator for combining terms

        Returns:
            List of search results
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Build FTS query based on scope
            fts_columns = self._get_fts_columns(scope)
            fts_query = self._build_fts_query(query, fts_columns, operator)

            # Build main search query
            sql, params = self._build_search_query(fts_query, filters, limit, offset)

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            return [self._row_to_search_result(row) for row in rows]

    def search_by_priority(
        self,
        min_priority: int = 1,
        max_priority: int = 5,
        urgency_levels: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[SearchResult]:
        """
        Search emails by priority and urgency levels.

        Args:
            min_priority: Minimum priority score (1-5)
            max_priority: Maximum priority score (1-5)
            urgency_levels: List of urgency levels to filter by
            limit: Maximum number of results

        Returns:
            List of search results
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            sql = """
                SELECT
                    e.id, e.message_id, e.subject, e.sender, e.recipients,
                    e.body_text, e.received_at,
                    c.priority_score, c.urgency_level, c.importance_level,
                    email_fts.rank as score
                FROM emails e
                JOIN classifications c ON e.id = c.email_id
                LEFT JOIN email_fts ON e.id = email_fts.rowid
                WHERE c.priority_score BETWEEN ? AND ?
            """

            params = [min_priority, max_priority]

            if urgency_levels:
                placeholders = ','.join(['?' for _ in urgency_levels])
                sql += f" AND c.urgency_level IN ({placeholders})"
                params.extend(urgency_levels)

            sql += " ORDER BY c.priority_score DESC, e.received_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            return [self._row_to_search_result(row) for row in rows]

    def search_by_sender(
        self,
        sender: str,
        limit: int = 50,
        include_body_search: bool = True
    ) -> List[SearchResult]:
        """
        Search emails by sender with optional full-text search.

        Args:
            sender: Sender email or name to search for
            limit: Maximum number of results
            include_body_search: Whether to also search in email body

        Returns:
            List of search results
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if include_body_search:
                sql = """
                    SELECT
                        e.id, e.message_id, e.subject, e.sender, e.recipients,
                        e.body_text, e.received_t,
                        email_fts.rank as score
                    FROM emails e
                    LEFT JOIN email_fts ON e.id = email_fts.rowid
                    WHERE e.sender LIKE ?
                    ORDER BY e.received_at DESC
                    LIMIT ?
                """
                params = [f"%{sender}%", limit]
            else:
                sql = """
                    SELECT
                        e.id, e.message_id, e.subject, e.sender, e.recipients,
                        e.body_text, e.received_at,
                        0 as score
                    FROM emails e
                    WHERE e.sender LIKE ?
                    ORDER BY e.received_at DESC
                    LIMIT ?
                """
                params = [f"%{sender}%", limit]

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            return [self._row_to_search_result(row) for row in rows]

    def search_by_date_range(
        self,
        start_date: str,
        end_date: str,
        limit: int = 50
    ) -> List[SearchResult]:
        """
        Search emails within a date range.

        Args:
            start_date: Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
            end_date: End date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
            limit: Maximum number of results

        Returns:
            List of search results
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            sql = """
                SELECT
                    e.id, e.message_id, e.subject, e.sender, e.recipients,
                    e.body_text, e.received_at,
                    0 as score
                FROM emails e
                WHERE e.received_at BETWEEN ? AND ?
                ORDER BY e.received_at DESC
                LIMIT ?
            """
            params = [start_date, end_date, limit]

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            return [self._row_to_search_result(row) for row in rows]

    def get_search_suggestions(
        self,
        partial_query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get search suggestions based on partial query.

        Args:
            partial_query: Partial search query
            limit: Maximum number of suggestions

        Returns:
            List of suggestion dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get subject suggestions
            cursor.execute("""
                SELECT DISTINCT subject, 'subject' as type
                FROM emails
                WHERE subject LIKE ?
                ORDER BY LENGTH(subject) ASC
                LIMIT ?
            """, (f"%{partial_query}%", limit // 2))

            subject_suggestions = [
                {"text": row[0], "type": row[1]}
                for row in cursor.fetchall()
            ]

            # Get sender suggestions
            cursor.execute("""
                SELECT DISTINCT sender, 'sender' as type
                FROM emails
                WHERE sender LIKE ?
                ORDER BY LENGTH(sender) ASC
                LIMIT ?
            """, (f"%{partial_query}%", limit // 2))

            sender_suggestions = [
                {"text": row[0], "type": row[1]}
                for row in cursor.fetchall()
            ]

            return subject_suggestions + sender_suggestions

    def _get_fts_columns(self, scope: SearchScope) -> List[str]:
        """Get FTS columns based on search scope."""
        if scope == SearchScope.ALL:
            return ["subject", "sender", "recipients", "body_text"]
        elif scope == SearchScope.SUBJECT:
            return ["subject"]
        elif scope == SearchScope.SENDER:
            return ["sender"]
        elif scope == SearchScope.RECIPIENTS:
            return ["recipients"]
        elif scope == SearchScope.BODY:
            return ["body_text"]
        else:
            return ["subject", "sender", "recipients", "body_text"]

    def _build_fts_query(
        self,
        query: str,
        columns: List[str],
        operator: SearchOperator
    ) -> str:
        """Build FTS query string."""
        # Clean and tokenize query
        terms = query.strip().split()
        if not terms:
            return ""

        # Build match query
        if len(columns) == 1:
            column_name = columns[0]
            match_terms = [f"{column_name}:{term}" for term in terms]
        else:
            match_terms = terms

        # Join terms with operator
        if operator == SearchOperator.AND:
            fts_query = " ".join(match_terms)
        elif operator == SearchOperator.OR:
            fts_query = " OR ".join(match_terms)
        elif operator == SearchOperator.NOT:
            if len(terms) > 1:
                fts_query = f"{terms[0]} NOT {' '.join(terms[1:])}"
            else:
                fts_query = terms[0]
        else:
            fts_query = " ".join(match_terms)

        return fts_query

    def _build_search_query(
        self,
        fts_query: str,
        filters: Optional[List[SearchFilter]],
        limit: int,
        offset: int
    ) -> Tuple[str, List[Any]]:
        """Build the complete search query with filters."""
        sql = """
            SELECT
                e.id, e.message_id, e.subject, e.sender, e.recipients,
                e.body_text, e.received_at,
                email_fts.rank as score
            FROM emails e
            LEFT JOIN email_fts ON e.id = email_fts.rowid
            WHERE email_fts MATCH ?
        """

        params = [fts_query]

        # Add filters
        if filters:
            for filter_obj in filters:
                if filter_obj.operator == "=":
                    sql += f" AND e.{filter_obj.field} = ?"
                elif filter_obj.operator == "LIKE":
                    sql += f" AND e.{filter_obj.field} LIKE ?"
                elif filter_obj.operator == ">":
                    sql += f" AND e.{filter_obj.field} > ?"
                elif filter_obj.operator == "<":
                    sql += f" AND e.{filter_obj.field} < ?"
                elif filter_obj.operator == ">=":
                    sql += f" AND e.{filter_obj.field} >= ?"
                elif filter_obj.operator == "<=":
                    sql += f" AND e.{filter_obj.field} <= ?"

                params.append(filter_obj.value)

        sql += " ORDER BY email_fts.rank DESC, e.received_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        return sql, params

    def _row_to_search_result(self, row: sqlite3.Row) -> SearchResult:
        """Convert database row to SearchResult."""
        return SearchResult(
            email_id=row['id'],
            message_id=row['message_id'],
            subject=row['subject'],
            sender=row['sender'],
            recipients=row['recipients'],
            body_text=row['body_text'],
            received_at=row['received_at'],
            score=row.get('score', 0.0),
            snippet=self._generate_snippet(row['body_text'])
        )

    def _generate_snippet(self, text: Optional[str], max_length: int = 200) -> Optional[str]:
        """Generate a snippet from text for search results."""
        if not text:
            return None

        if len(text) <= max_length:
            return text

        # Simple truncation with ellipsis
        return text[:max_length-3] + "..."

    def rebuild_fts_index(self) -> None:
        """Rebuild the full-text search index."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Rebuild FTS index
            cursor.execute("INSERT INTO email_fts(email_fts) VALUES('rebuild');")

            # Optimize the index
            cursor.execute("INSERT INTO email_fts(email_fts) VALUES('optimize');")

            conn.commit()