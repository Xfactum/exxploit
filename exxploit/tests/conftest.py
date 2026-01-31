"""
Pytest fixtures for exxploit tests.
"""

import pytest
from pathlib import Path


@pytest.fixture
def tmp_log_dir(tmp_path):
    """Create a temporary directory for test logs."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


@pytest.fixture
def sample_vulnerable_html():
    """Sample HTML with XSS vulnerability."""
    return """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Search Results</h1>
        <div id="results">Results for: <test></div>
        <script>var q = "<test>";</script>
    </body>
    </html>
    """


@pytest.fixture
def sample_safe_html():
    """Sample HTML without XSS vulnerability."""
    return """
    <html>
    <head><title>Safe Page</title></head>
    <body>
        <h1>Welcome</h1>
        <p>This page sanitizes all input.</p>
    </body>
    </html>
    """
