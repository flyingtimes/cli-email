"""
Main entry point for Email Priority Manager package.

This module provides the primary interface for the email priority manager application.
"""

from .cli.main import main

__all__ = ["main"]

if __name__ == "__main__":
    main()