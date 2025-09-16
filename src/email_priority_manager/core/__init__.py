"""
Core functionality for Email Priority Manager.

Contains the main email processing logic and classification algorithms.
"""

from .processor import EmailProcessor
from .classifier import EmailClassifier
from .email_client import EmailClient

__all__ = ["EmailProcessor", "EmailClassifier", "EmailClient"]