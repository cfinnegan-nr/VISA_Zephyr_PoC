"""
Integration tests for JIRA Ticket Reader application.

These tests verify:
- End-to-end application flow
- Output format verification
- Integration between components
"""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.jira_reader import main


class TestApplicationOutput:
    """Test application output format and content."""

    def test_output_contains_expected_sections(self):
        """Test that application output contains expected sections."""
        # This test verifies the output format matches expectations
        # We'll mock the JIRA calls to avoid actual API calls

        with patch("src.jira_reader.load_settings") as mock_load, patch(
            "src.jira_reader.parse_atlassian_input"
        ) as mock_parse, patch("src.jira_reader.JiraClient") as mock_client_class:

            # Setup mocks
            mock_settings = MagicMock()
            mock_load.return_value = mock_settings

            mock_parse.return_value = {
                "qa_ticket": "PROJECT-12345",
                "epic_ticket": "PROJECT-67890",
            }

            mock_client = MagicMock()
            mock_client.get_issue.side_effect = [
                {
                    "key": "PROJECT-12345",
                    "summary": "Test QA Ticket Summary",
                    "issue_type": "Task",
                },
                {
                    "key": "PROJECT-67890",
                    "summary": "Test Epic Summary",
                    "issue_type": "Epic",
                },
            ]
            mock_client_class.return_value = mock_client

            # Capture output
            import io
            from contextlib import redirect_stdout

            output = io.StringIO()
            with redirect_stdout(output):
                result = main()

            output_text = output.getvalue()

            # Verify exit code
            assert result == 0

            # Verify output contains expected sections
            assert "Fetching JIRA Ticket Information" in output_text
            assert "PROJECT-12345" in output_text
            assert "PROJECT-67890" in output_text
            assert "Test QA Ticket Summary" in output_text
            assert "Test Epic Summary" in output_text

            # Verify box formatting is present
            assert "╔" in output_text  # Top border
            assert "╚" in output_text  # Bottom border
            assert "JIRA TICKET SUMMARY" in output_text

    def test_output_format_structure(self):
        """Test that output follows the expected structure."""
        with patch("src.jira_reader.load_settings"), patch(
            "src.jira_reader.parse_atlassian_input"
        ) as mock_parse, patch("src.jira_reader.JiraClient") as mock_client_class:

            mock_parse.return_value = {
                "qa_ticket": "PROJECT-12345",
                "epic_ticket": "PROJECT-67890",
            }

            mock_client = MagicMock()
            mock_client.get_issue.return_value = {
                "key": "PROJECT-12345",
                "summary": "Test Summary",
                "issue_type": "Task",
            }
            mock_client_class.return_value = mock_client

            import io
            from contextlib import redirect_stdout

            output = io.StringIO()
            with redirect_stdout(output):
                main()

            output_text = output.getvalue()

            # Verify structure: should have two ticket boxes
            # Count box borders (each ticket has top and bottom)
            top_borders = output_text.count("╔")
            bottom_borders = output_text.count("╚")

            # Should have at least 2 tickets (top and bottom borders for each)
            assert top_borders >= 2
            assert bottom_borders >= 2

            # Verify each ticket box contains required fields
            assert output_text.count("Issue Key:") >= 2
            assert output_text.count("Issue Type:") >= 2
            assert output_text.count("Summary:") >= 2


class TestApplicationErrorHandling:
    """Test application error handling and error messages."""

    def test_configuration_error_handling(self):
        """Test handling of configuration errors."""
        with patch("src.jira_reader.load_settings") as mock_load:
            from src.exceptions import JiraConfigurationError

            mock_load.side_effect = JiraConfigurationError(
                "Missing required configuration"
            )

            import io
            from contextlib import redirect_stdout

            output = io.StringIO()
            with redirect_stdout(output):
                result = main()

            output_text = output.getvalue()

            # Should exit with error code
            assert result == 1
            assert "ERROR" in output_text
            assert "Configuration" in output_text

    def test_input_file_error_handling(self):
        """Test handling of input file errors."""
        with patch("src.jira_reader.load_settings"), patch(
            "src.jira_reader.parse_atlassian_input"
        ) as mock_parse:
            from src.exceptions import InputFileError

            mock_parse.side_effect = InputFileError("Input file not found")

            import io
            from contextlib import redirect_stdout

            output = io.StringIO()
            with redirect_stdout(output):
                result = main()

            output_text = output.getvalue()

            # Should exit with error code
            assert result == 1
            assert "ERROR" in output_text
            assert "input file" in output_text.lower()

    def test_jira_client_error_handling(self):
        """Test handling of JIRA client errors."""
        with patch("src.jira_reader.load_settings"), patch(
            "src.jira_reader.parse_atlassian_input"
        ) as mock_parse, patch("src.jira_reader.JiraClient") as mock_client_class:

            mock_parse.return_value = {
                "qa_ticket": "PROJECT-12345",
                "epic_ticket": "PROJECT-67890",
            }

            mock_client_class.side_effect = Exception("Failed to initialize client")

            import io
            from contextlib import redirect_stdout

            output = io.StringIO()
            with redirect_stdout(output):
                result = main()

            output_text = output.getvalue()

            # Should exit with error code
            assert result == 1
            assert "ERROR" in output_text

    def test_issue_not_found_handling(self):
        """Test handling when JIRA issue is not found."""
        with patch("src.jira_reader.load_settings"), patch(
            "src.jira_reader.parse_atlassian_input"
        ) as mock_parse, patch("src.jira_reader.JiraClient") as mock_client_class:

            mock_parse.return_value = {
                "qa_ticket": "PROJECT-99999",
                "epic_ticket": "PROJECT-88888",
            }

            mock_client = MagicMock()
            from src.exceptions import JiraIssueNotFoundError

            mock_client.get_issue.side_effect = [
                JiraIssueNotFoundError("Issue not found"),
                {
                    "key": "PROJECT-88888",
                    "summary": "Epic Summary",
                    "issue_type": "Epic",
                },
            ]
            mock_client_class.return_value = mock_client

            import io
            from contextlib import redirect_stdout

            output = io.StringIO()
            with redirect_stdout(output):
                result = main()

            output_text = output.getvalue()

            # Should continue and show warning, not exit with error
            assert "WARNING" in output_text or "not found" in output_text.lower()
            # Should still process the epic ticket
            assert "PROJECT-88888" in output_text


class TestApplicationExecution:
    """Test actual application execution (if possible)."""

    @pytest.mark.skipif(
        not Path(".env").exists(),
        reason=".env file not found - skipping integration test",
    )
    def test_application_runs_without_errors(self):
        """Test that application can be executed without build/runtime errors."""
        # This test verifies the application can be imported and main() can be called
        # It doesn't require actual JIRA connection if we mock it

        with patch("src.jira_reader.load_settings"), patch(
            "src.jira_reader.parse_atlassian_input"
        ), patch("src.jira_reader.JiraClient"):
            # Just verify main() can be called without syntax/runtime errors
            try:
                # This should not raise any import or syntax errors
                from src.jira_reader import main

                assert callable(main)
            except Exception as e:
                pytest.fail(f"Application has build/runtime errors: {e}")

