"""
Database models and data classes for email priority manager.
Provides structured data access and validation for all entities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import re


@dataclass
class Email:
    """Represents an email message."""
    id: Optional[int] = None
    message_id: str = ""
    subject: str = ""
    sender: str = ""
    recipients: str = ""
    cc: Optional[str] = None
    bcc: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    received_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    size_bytes: Optional[int] = None
    has_attachments: bool = False
    is_read: bool = False
    is_flagged: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate email data after initialization."""
        if not self.message_id:
            raise ValueError("message_id is required")
        if not self.subject:
            raise ValueError("subject is required")
        if not self.sender:
            raise ValueError("sender is required")
        if not self.recipients:
            raise ValueError("recipients is required")

    @property
    def recipient_list(self) -> List[str]:
        """Parse recipients string into a list."""
        return [email.strip() for email in self.recipients.split(',') if email.strip()]

    @property
    def cc_list(self) -> List[str]:
        """Parse CC string into a list."""
        if not self.cc:
            return []
        return [email.strip() for email in self.cc.split(',') if email.strip()]

    @property
    def bcc_list(self) -> List[str]:
        """Parse BCC string into a list."""
        if not self.bcc:
            return []
        return [email.strip() for email in self.bcc.split(',') if email.strip()]

    def to_dict(self) -> Dict[str, Any]:
        """Convert email to dictionary."""
        return {
            'id': self.id,
            'message_id': self.message_id,
            'subject': self.subject,
            'sender': self.sender,
            'recipients': self.recipients,
            'cc': self.cc,
            'bcc': self.bcc,
            'body_text': self.body_text,
            'body_html': self.body_html,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'size_bytes': self.size_bytes,
            'has_attachments': self.has_attachments,
            'is_read': self.is_read,
            'is_flagged': self.is_flagged,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Email':
        """Create email from dictionary."""
        # Handle datetime fields
        for date_field in ['received_at', 'sent_at', 'created_at', 'updated_at']:
            if data.get(date_field) and isinstance(data[date_field], str):
                data[date_field] = datetime.fromisoformat(data[date_field])

        return cls(**data)

    def get_searchable_text(self) -> str:
        """Get combined text for full-text search."""
        parts = [self.subject, self.sender, self.recipients]
        if self.cc:
            parts.append(self.cc)
        if self.body_text:
            parts.append(self.body_text)
        return ' '.join(filter(None, parts))


@dataclass
class Attachment:
    """Represents an email attachment."""
    id: Optional[int] = None
    email_id: int = 0
    filename: str = ""
    file_path: str = ""
    size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    content_hash: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate attachment data after initialization."""
        if not self.email_id:
            raise ValueError("email_id is required")
        if not self.filename:
            raise ValueError("filename is required")
        if not self.file_path:
            raise ValueError("file_path is required")

    def to_dict(self) -> Dict[str, Any]:
        """Convert attachment to dictionary."""
        return {
            'id': self.id,
            'email_id': self.email_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'size_bytes': self.size_bytes,
            'mime_type': self.mime_type,
            'content_hash': self.content_hash,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Attachment':
        """Create attachment from dictionary."""
        if data.get('created_at') and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

    @property
    def file_extension(self) -> str:
        """Get file extension from filename."""
        match = re.search(r'\.([^.]+)$', self.filename)
        return match.group(1).lower() if match else ''

    @property
    def is_document(self) -> bool:
        """Check if attachment is a document."""
        doc_extensions = {'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'}
        return self.file_extension in doc_extensions

    @property
    def is_image(self) -> bool:
        """Check if attachment is an image."""
        img_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp'}
        return self.file_extension in img_extensions

    @property
    def is_archive(self) -> bool:
        """Check if attachment is an archive."""
        archive_extensions = {'zip', 'rar', '7z', 'tar', 'gz', 'bz2'}
        return self.file_extension in archive_extensions


@dataclass
class Classification:
    """Represents an email classification."""
    id: Optional[int] = None
    email_id: int = 0
    priority_score: int = 3  # 1-5 scale
    urgency_level: str = "medium"  # low, medium, high, critical
    importance_level: str = "medium"  # low, medium, high, critical
    classification_type: str = ""
    confidence_score: float = 0.0  # 0.0-1.0
    ai_analysis: Optional[str] = None
    classified_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate classification data after initialization."""
        if not self.email_id:
            raise ValueError("email_id is required")
        if not (1 <= self.priority_score <= 5):
            raise ValueError("priority_score must be between 1 and 5")
        if self.urgency_level not in ['low', 'medium', 'high', 'critical']:
            raise ValueError("urgency_level must be one of: low, medium, high, critical")
        if self.importance_level not in ['low', 'medium', 'high', 'critical']:
            raise ValueError("importance_level must be one of: low, medium, high, critical")
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("confidence_score must be between 0.0 and 1.0")

    def to_dict(self) -> Dict[str, Any]:
        """Convert classification to dictionary."""
        return {
            'id': self.id,
            'email_id': self.email_id,
            'priority_score': self.priority_score,
            'urgency_level': self.urgency_level,
            'importance_level': self.importance_level,
            'classification_type': self.classification_type,
            'confidence_score': self.confidence_score,
            'ai_analysis': self.ai_analysis,
            'classified_at': self.classified_at.isoformat() if self.classified_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Classification':
        """Create classification from dictionary."""
        for date_field in ['classified_at', 'updated_at']:
            if data.get(date_field) and isinstance(data[date_field], str):
                data[date_field] = datetime.fromisoformat(data[date_field])
        return cls(**data)

    @property
    def overall_priority(self) -> float:
        """Calculate overall priority score combining urgency and importance."""
        urgency_weights = {'low': 0.25, 'medium': 0.5, 'high': 0.75, 'critical': 1.0}
        importance_weights = {'low': 0.25, 'medium': 0.5, 'high': 0.75, 'critical': 1.0}

        urgency_score = urgency_weights.get(self.urgency_level, 0.5)
        importance_score = importance_weights.get(self.importance_level, 0.5)

        return (urgency_score + importance_score) / 2 * self.confidence_score


@dataclass
class Rule:
    """Represents a user-defined rule for email processing."""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    rule_type: str = "custom"  # sender, keyword, time, custom
    condition: str = ""
    action: str = "classify"  # classify, tag, flag, move
    priority: int = 0  # Higher priority rules run first
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate rule data after initialization."""
        if not self.name:
            raise ValueError("name is required")
        if self.rule_type not in ['sender', 'keyword', 'time', 'custom']:
            raise ValueError("rule_type must be one of: sender, keyword, time, custom")
        if not self.condition:
            raise ValueError("condition is required")
        if self.action not in ['classify', 'tag', 'flag', 'move']:
            raise ValueError("action must be one of: classify, tag, flag, move")

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'rule_type': self.rule_type,
            'condition': self.condition,
            'action': self.action,
            'priority': self.priority,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """Create rule from dictionary."""
        for date_field in ['created_at', 'updated_at']:
            if data.get(date_field) and isinstance(data[date_field], str):
                data[date_field] = datetime.fromisoformat(data[date_field])
        return cls(**data)

    def matches_email(self, email: Email) -> bool:
        """Check if this rule matches the given email."""
        if not self.is_active:
            return False

        try:
            if self.rule_type == 'sender':
                return self.condition.lower() in email.sender.lower()
            elif self.rule_type == 'keyword':
                search_text = email.get_searchable_text().lower()
                return self.condition.lower() in search_text
            elif self.rule_type == 'time':
                # Simple time-based matching (can be enhanced)
                return self._evaluate_time_condition(email)
            elif self.rule_type == 'custom':
                return self._evaluate_custom_condition(email)
        except Exception as e:
            # Log error but don't crash
            return False

        return False

    def _evaluate_time_condition(self, email: Email) -> bool:
        """Evaluate time-based condition."""
        # Simple implementation - can be enhanced with complex time parsing
        now = datetime.now()
        condition = self.condition.lower()

        if 'today' in condition:
            return email.received_at.date() == now.date()
        elif 'this week' in condition:
            week_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - \
                        timedelta(days=now.weekday())
            return email.received_at >= week_start
        elif 'this month' in condition:
            return email.received_at.month == now.month and email.received_at.year == now.year

        return False

    def _evaluate_custom_condition(self, email: Email) -> bool:
        """Evaluate custom condition (simplified implementation)."""
        # This could be enhanced with a proper expression evaluator
        try:
            # For now, treat as a simple keyword search
            search_text = email.get_searchable_text().lower()
            return self.condition.lower() in search_text
        except:
            return False


@dataclass
class History:
    """Represents a history entry for audit trail."""
    id: Optional[int] = None
    email_id: Optional[int] = None
    action_type: str = ""
    action_details: Optional[str] = None
    performed_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate history data after initialization."""
        if not self.action_type:
            raise ValueError("action_type is required")

    def to_dict(self) -> Dict[str, Any]:
        """Convert history to dictionary."""
        return {
            'id': self.id,
            'email_id': self.email_id,
            'action_type': self.action_type,
            'action_details': self.action_details,
            'performed_at': self.performed_at.isoformat() if self.performed_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'History':
        """Create history from dictionary."""
        if data.get('performed_at') and isinstance(data['performed_at'], str):
            data['performed_at'] = datetime.fromisoformat(data['performed_at'])
        return cls(**data)


@dataclass
class Tag:
    """Represents an email tag."""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    color: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate tag data after initialization."""
        if not self.name:
            raise ValueError("name is required")

    def to_dict(self) -> Dict[str, Any]:
        """Convert tag to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tag':
        """Create tag from dictionary."""
        if data.get('created_at') and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class EmailTag:
    """Represents a many-to-many relationship between emails and tags."""
    email_id: int = 0
    tag_id: int = 0
    assigned_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate email-tag data after initialization."""
        if not self.email_id:
            raise ValueError("email_id is required")
        if not self.tag_id:
            raise ValueError("tag_id is required")

    def to_dict(self) -> Dict[str, Any]:
        """Convert email-tag to dictionary."""
        return {
            'email_id': self.email_id,
            'tag_id': self.tag_id,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailTag':
        """Create email-tag from dictionary."""
        if data.get('assigned_at') and isinstance(data['assigned_at'], str):
            data['assigned_at'] = datetime.fromisoformat(data['assigned_at'])
        return cls(**data)


# Model factory functions
def create_email_from_row(row) -> Email:
    """Create Email object from database row."""
    columns = ['id', 'message_id', 'subject', 'sender', 'recipients', 'cc', 'bcc',
              'body_text', 'body_html', 'received_at', 'sent_at', 'size_bytes',
              'has_attachments', 'is_read', 'is_flagged', 'created_at', 'updated_at']

    data = dict(zip(columns, row))
    return Email.from_dict(data)


def create_attachment_from_row(row) -> Attachment:
    """Create Attachment object from database row."""
    columns = ['id', 'email_id', 'filename', 'file_path', 'size_bytes',
              'mime_type', 'content_hash', 'created_at']

    data = dict(zip(columns, row))
    return Attachment.from_dict(data)


def create_classification_from_row(row) -> Classification:
    """Create Classification object from database row."""
    columns = ['id', 'email_id', 'priority_score', 'urgency_level', 'importance_level',
              'classification_type', 'confidence_score', 'ai_analysis',
              'classified_at', 'updated_at']

    data = dict(zip(columns, row))
    return Classification.from_dict(data)


def create_rule_from_row(row) -> Rule:
    """Create Rule object from database row."""
    columns = ['id', 'name', 'description', 'rule_type', 'condition', 'action',
              'priority', 'is_active', 'created_at', 'updated_at']

    data = dict(zip(columns, row))
    return Rule.from_dict(data)


def create_history_from_row(row) -> History:
    """Create History object from database row."""
    columns = ['id', 'email_id', 'action_type', 'action_details', 'performed_at']

    data = dict(zip(columns, row))
    return History.from_dict(data)


def create_tag_from_row(row) -> Tag:
    """Create Tag object from database row."""
    columns = ['id', 'name', 'description', 'color', 'created_at']

    data = dict(zip(columns, row))
    return Tag.from_dict(data)


def create_email_tag_from_row(row) -> EmailTag:
    """Create EmailTag object from database row."""
    columns = ['email_id', 'tag_id', 'assigned_at']

    data = dict(zip(columns, row))
    return EmailTag.from_dict(data)