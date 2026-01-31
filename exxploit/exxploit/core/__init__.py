"""
exxploit.core - Core modules for payload generation and scanning.

This package provides the core functionality:
- PayloadFactory: Generate and obfuscate XSS payloads.
- Scanner: Find XSS injection points in web applications.
- Stealth: Anti-detection and human-like behavior.
- Automation: Playwright-based browser automation (GhostAuditBot).
"""

__author__ = "HACKThief"
__version__ = "1.0.0"

from .factory import PayloadFactory
from .scanner import Scanner

__all__ = ["PayloadFactory", "Scanner"]
