"""
AI module for Email Priority Manager.

Provides AI-powered email classification and prioritization using BigModel.cn API.
"""

from .bigmodel import BigModelClient
from .nlp import TextProcessor

__all__ = ["BigModelClient", "TextProcessor"]