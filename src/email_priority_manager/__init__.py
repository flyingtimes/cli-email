"""
Email Priority Manager

A sophisticated email management system that prioritizes emails using AI analysis
and provides intelligent categorization and processing.
"""

__version__ = "0.1.0"
__author__ = "Email Priority Manager Team"
__email__ = "support@emailprioritymanager.com"

from .config.settings import get_settings
from .config.models import AppConfig

__all__ = ["get_settings", "AppConfig", "__version__"]