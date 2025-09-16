"""
Configuration module for Email Priority Manager.

Manages application settings, environment variables, and configuration files.
"""

from .settings import Settings
from .secrets import SecretsManager

__all__ = ["Settings", "SecretsManager"]