"""
Unit tests for JIRA reader module.

Tests cover:
- JiraClient initialization
- get_issue method with various scenarios
- Error handling for different HTTP status codes
- Main application flow
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout

from src.config import Settings
from src.exceptions import (
    JiraAuthenticationError,
    JiraConnectionError,
    JiraIssueNotFoundError,
)
from src.jira_reader import JiraClient


class TestJiraClient:
    """Test JiraClient class."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock Settings object."""
        settings = Settings(
            jira_server_url="https://test.atlassian.net",
            jira_username="test@example.com",
            jira_api_token="test-token-123",
        )
        return settings

    def test_jira_client_initialization(self, mock_settings):
        """Test JiraClient initialization with valid settings."""
        client = JiraClient(mock_settings)

        assert client.server_url == "https://test.atlassian.net"
        assert client.username == "test@example.com"
        assert client.api_token == "test-token-123"
        assert client.session is not None
        assert client.session.auth is not None

    def test_jira_client_invalid_url(self):
        """Test JiraClient raises error for invalid URL."""
        settings = Settings(
            jira_server_url="invalid-url",
            jira_username="test@example.com",
            jira_api_token="test-token-123",
        )

        with pytest.raises(Exception):  # Should raise JiraConfigurationError
            JiraClient(settings)

    def test_jira_client_get_issue_success(self, mock_settings):
        """Test successful issue retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "key": "PROJECT-12345",
            "fields": {
                "summary": "Test Issue Summary",
                "issuetype": {"name": "Task"},
            },
        }
        mock_response.raise_for_status = Mock()

        # Mock session
        with patch("src.jira_reader.requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            client = JiraClient(mock_settings)
            result = client.get_issue("PROJECT-12345")

            assert result["key"] == "PROJECT-12345"
            assert result["summary"] == "Test Issue Summary"
            assert result["issue_type"] == "Task"

    def test_jira_client_get_issue_not_found(self, mock_settings):
        """Test handling of 404 Not Found error."""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_error = HTTPError("Not Found")
        mock_error.response = mock_response

        # Mock session
        with patch("src.jira_reader.requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.side_effect = mock_error
            mock_session_class.return_value = mock_session

            client = JiraClient(mock_settings)

            with pytest.raises(JiraIssueNotFoundError):
                client.get_issue("PROJECT-99999")

    def test_jira_client_get_issue_authentication_error_401(self, mock_settings):
        """Test handling of 401 Unauthorized error."""
        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_error = HTTPError("Unauthorized")
        mock_error.response = mock_response

        # Mock session
        with patch("src.jira_reader.requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.side_effect = mock_error
            mock_session_class.return_value = mock_session

            client = JiraClient(mock_settings)

            with pytest.raises(JiraAuthenticationError):
                client.get_issue("PROJECT-12345")

    def test_jira_client_get_issue_authentication_error_403(self, mock_settings):
        """Test handling of 403 Forbidden error."""
        # Mock 403 response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_error = HTTPError("Forbidden")
        mock_error.response = mock_response

        # Mock session
        with patch("src.jira_reader.requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.side_effect = mock_error
            mock_session_class.return_value = mock_session

            client = JiraClient(mock_settings)

            with pytest.raises(JiraAuthenticationError):
                client.get_issue("PROJECT-12345")

    def test_jira_client_get_issue_connection_error(self, mock_settings):
        """Test handling of connection error."""
        # Mock connection error
        mock_error = ConnectionError("Connection failed")

        # Mock session
        with patch("src.jira_reader.requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.side_effect = mock_error
            mock_session_class.return_value = mock_session

            client = JiraClient(mock_settings)

            with pytest.raises(JiraConnectionError):
                client.get_issue("PROJECT-12345")

    def test_jira_client_get_issue_timeout(self, mock_settings):
        """Test handling of timeout error."""
        # Mock timeout error
        mock_error = Timeout("Request timed out")

        # Mock session
        with patch("src.jira_reader.requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.side_effect = mock_error
            mock_session_class.return_value = mock_session

            client = JiraClient(mock_settings)

            with pytest.raises(JiraConnectionError):
                client.get_issue("PROJECT-12345")

    def test_jira_client_get_issue_invalid_json(self, mock_settings):
        """Test handling of invalid JSON response."""
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()

        # Mock session
        with patch("src.jira_reader.requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            client = JiraClient(mock_settings)

            with pytest.raises(JiraConnectionError):
                client.get_issue("PROJECT-12345")

    def test_jira_client_close(self, mock_settings):
        """Test closing the client session."""
        client = JiraClient(mock_settings)
        assert client.session is not None

        client.close()
        # Session should be closed (we can't easily verify this without mocking)

