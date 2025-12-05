"""
Unit tests for configuration management module.

Tests cover:
- Loading settings from .env file
- Validation of required fields
- Error handling for missing/invalid configuration
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from src.config import Settings, load_settings
from src.exceptions import JiraConfigurationError


class TestSettings:
    """Test Settings class validation."""

    def test_settings_valid_creation(self):
        """Test creating Settings with valid values."""
        with patch.dict(
            os.environ,
            {
                "JIRA_SERVER_URL": "https://test.atlassian.net",
                "JIRA_USERNAME": "test@example.com",
                "JIRA_API_TOKEN": "test-token-123",
            },
        ):
            settings = Settings()
            assert settings.jira_server_url == "https://test.atlassian.net"
            assert settings.jira_username == "test@example.com"
            assert settings.jira_api_token == "test-token-123"

    def test_settings_missing_server_url(self):
        """Test Settings raises error when JIRA_SERVER_URL is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_settings_missing_username(self):
        """Test Settings raises error when JIRA_USERNAME is missing."""
        with patch.dict(
            os.environ,
            {
                "JIRA_SERVER_URL": "https://test.atlassian.net",
                "JIRA_API_TOKEN": "test-token-123",
            },
        ):
            with pytest.raises(ValidationError):
                Settings()

    def test_settings_missing_api_token(self):
        """Test Settings raises error when JIRA_API_TOKEN is missing."""
        with patch.dict(
            os.environ,
            {
                "JIRA_SERVER_URL": "https://test.atlassian.net",
                "JIRA_USERNAME": "test@example.com",
            },
        ):
            with pytest.raises(ValidationError):
                Settings()

    def test_settings_case_insensitive(self):
        """Test Settings handles case-insensitive environment variables."""
        with patch.dict(
            os.environ,
            {
                "jira_server_url": "https://test.atlassian.net",
                "jira_username": "test@example.com",
                "jira_api_token": "test-token-123",
            },
        ):
            settings = Settings()
            assert settings.jira_server_url == "https://test.atlassian.net"
            assert settings.jira_username == "test@example.com"
            assert settings.jira_api_token == "test-token-123"


class TestLoadSettings:
    """Test load_settings function."""

    def test_load_settings_from_env_file(self, tmp_path, monkeypatch):
        """Test loading settings from a .env file."""
        # Create temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text(
            "JIRA_SERVER_URL=https://test.atlassian.net\n"
            "JIRA_USERNAME=test@example.com\n"
            "JIRA_API_TOKEN=test-token-123\n"
        )

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Mock the project root to be the temp directory
        with patch("src.config.Path") as mock_path:
            mock_env_path = tmp_path / ".env"
            mock_path.return_value.parent.parent = tmp_path

            # Clear environment variables
            with patch.dict(os.environ, {}, clear=True):
                settings = load_settings()
                assert settings.jira_server_url == "https://test.atlassian.net"
                assert settings.jira_username == "test@example.com"
                assert settings.jira_api_token == "test-token-123"

    def test_load_settings_missing_env_file(self, tmp_path, monkeypatch):
        """Test load_settings when .env file doesn't exist."""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            # Mock the path resolution in load_settings
            with patch("src.config.Path") as mock_path_class:
                # Mock __file__ path resolution
                mock_file_path = MagicMock()
                mock_file_path.parent.parent = tmp_path
                mock_path_class.return_value = mock_file_path
                
                # Mock load_dotenv to not load anything
                with patch("src.config.load_dotenv", return_value=False):
                    with pytest.raises(JiraConfigurationError) as exc_info:
                        load_settings()
                    assert "JIRA_SERVER_URL" in str(exc_info.value)
                    assert "JIRA_USERNAME" in str(exc_info.value)
                    assert "JIRA_API_TOKEN" in str(exc_info.value)

    def test_load_settings_invalid_url(self, tmp_path, monkeypatch):
        """Test load_settings validates URL format."""
        # Create temporary .env file with invalid URL
        env_file = tmp_path / ".env"
        env_file.write_text(
            "JIRA_SERVER_URL=invalid-url\n"
            "JIRA_USERNAME=test@example.com\n"
            "JIRA_API_TOKEN=test-token-123\n"
        )

        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            # Mock Path(__file__).parent.parent to point to tmp_path
            with patch("src.config.Path") as mock_path_class:
                mock_path = MagicMock()
                mock_path.parent.parent = tmp_path
                mock_path_class.return_value = mock_path
                
                with pytest.raises(JiraConfigurationError) as exc_info:
                    load_settings()
                assert "http:// or https://" in str(exc_info.value)

    def test_load_settings_from_system_env(self):
        """Test loading settings from system environment variables."""
        with patch.dict(
            os.environ,
            {
                "JIRA_SERVER_URL": "https://test.atlassian.net",
                "JIRA_USERNAME": "test@example.com",
                "JIRA_API_TOKEN": "test-token-123",
            },
        ):
            # Mock that .env file doesn't exist
            with patch("pathlib.Path.exists", return_value=False):
                settings = load_settings()
                assert settings.jira_server_url == "https://test.atlassian.net"
                assert settings.jira_username == "test@example.com"
                assert settings.jira_api_token == "test-token-123"

    def test_load_settings_empty_env_file(self, tmp_path, monkeypatch):
        """Test load_settings with empty .env file."""
        # Create empty .env file
        env_file = tmp_path / ".env"
        env_file.write_text("")

        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            # Mock Path(__file__).parent.parent to point to tmp_path
            with patch("src.config.Path") as mock_path_class:
                mock_path = MagicMock()
                mock_path.parent.parent = tmp_path
                mock_path_class.return_value = mock_path
                
                with pytest.raises(JiraConfigurationError):
                    load_settings()

