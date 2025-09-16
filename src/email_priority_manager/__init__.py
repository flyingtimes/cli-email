"""
Email Priority Manager - AI-powered email prioritization system.

This package provides intelligent email management using BigModel.cn API
to automatically categorize and prioritize incoming emails.
"""

__version__ = "0.1.0"
__author__ = "Email Priority Manager Team"
__email__ = "team@example.com"

from .core.processor import EmailProcessor
from .core.classifier import EmailClassifier
from .database.models import Email, Priority
from .config.settings import Settings

__all__ = [
    "EmailProcessor",
    "EmailClassifier",
    "Email",
    "Priority",
    "Settings",
]