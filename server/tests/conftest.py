"""Pytest fixtures for OpenBrowser server tests."""

import pytest


@pytest.fixture
def sample_fixture():
    """A sample fixture for testing the test framework setup."""
    return {"status": "ok"}


@pytest.fixture
def mock_conversation_id():
    """Sample conversation ID for testing."""
    return "test-conversation-123"
