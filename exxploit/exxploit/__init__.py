"""
exxploit - High-Evasion XSS Payload Toolkit

A professional CLI tool for XSS payload generation, injection testing, 
and security auditing with advanced evasion capabilities.
"""

__version__ = "1.0.0"
__author__ = "HACKThief"

from .core.factory import PayloadFactory
from .core.scanner import Scanner

__all__ = ["PayloadFactory", "Scanner", "__version__"]
