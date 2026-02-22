"""
Unit tests for utility functions.

Tests cover:
- Parsing AtlassianInput.txt file
- Formatting ticket output
- Error handling for invalid input
"""

import tempfile
from pathlib import Path

import pytest

from src.exceptions import InputFileError
from src.utils import format_ticket_output, parse_atlassian_input


class TestParseAtlassianInput:
    """Test parse_atlassian_input function."""

    def test_parse_valid_input_file(self, tmp_path):
        """Test parsing a valid input file."""
        # Create temporary input file
        input_file = tmp_path / "AtlassianInput.txt"
        input_file.write_text(
            "JIRA QA Ticket:PROJECT-12345\nEPIC Ticket:PROJECT-67890\n"
        )

        result = parse_atlassian_input(input_file)

        assert result["qa_ticket"] == "PROJECT-12345"
        assert result["epic_ticket"] == "PROJECT-67890"

    def test_parse_input_with_whitespace(self, tmp_path):
        """Test parsing input file with extra whitespace."""
        input_file = tmp_path / "AtlassianInput.txt"
        input_file.write_text(
            "JIRA QA Ticket: PROJECT-12345 \nEPIC Ticket: PROJECT-67890 \n"
        )

        result = parse_atlassian_input(input_file)

        assert result["qa_ticket"] == "PROJECT-12345"
        assert result["epic_ticket"] == "PROJECT-67890"

    def test_parse_input_with_empty_lines(self, tmp_path):
        """Test parsing input file with empty lines."""
        input_file = tmp_path / "AtlassianInput.txt"
        input_file.write_text(
            "\nJIRA QA Ticket:PROJECT-12345\n\nEPIC Ticket:PROJECT-67890\n\n"
        )

        result = parse_atlassian_input(input_file)

        assert result["qa_ticket"] == "PROJECT-12345"
        assert result["epic_ticket"] == "PROJECT-67890"

    def test_parse_input_file_not_found(self, tmp_path):
        """Test parsing when input file doesn't exist."""
        non_existent_file = tmp_path / "NonExistent.txt"

        with pytest.raises(InputFileError) as exc_info:
            parse_atlassian_input(non_existent_file)
        assert "not found" in str(exc_info.value).lower()

    def test_parse_input_missing_qa_ticket(self, tmp_path):
        """Test parsing input file missing QA ticket."""
        input_file = tmp_path / "AtlassianInput.txt"
        input_file.write_text("EPIC Ticket:PROJECT-67890\n")

        with pytest.raises(InputFileError) as exc_info:
            parse_atlassian_input(input_file)
        assert "QA Ticket" in str(exc_info.value)

    def test_parse_input_missing_epic_ticket(self, tmp_path):
        """Test parsing input file missing Epic ticket."""
        input_file = tmp_path / "AtlassianInput.txt"
        input_file.write_text("JIRA QA Ticket:PROJECT-12345\n")

        with pytest.raises(InputFileError) as exc_info:
            parse_atlassian_input(input_file)
        assert "EPIC Ticket" in str(exc_info.value)

    def test_parse_input_invalid_format(self, tmp_path):
        """Test parsing input file with invalid format."""
        input_file = tmp_path / "AtlassianInput.txt"
        input_file.write_text("Invalid line format\n")

        with pytest.raises(InputFileError):
            parse_atlassian_input(input_file)

    def test_parse_input_empty_ticket_key(self, tmp_path):
        """Test parsing input file with empty ticket key."""
        input_file = tmp_path / "AtlassianInput.txt"
        input_file.write_text("JIRA QA Ticket:\nEPIC Ticket:PROJECT-67890\n")

        with pytest.raises(InputFileError) as exc_info:
            parse_atlassian_input(input_file)
        # Should raise error about missing QA ticket (empty key is treated as missing)
        assert "QA Ticket" in str(exc_info.value) or "Invalid" in str(exc_info.value) or "format" in str(exc_info.value)

    def test_parse_input_case_sensitivity(self, tmp_path):
        """Test parsing is case-sensitive for labels."""
        input_file = tmp_path / "AtlassianInput.txt"
        input_file.write_text(
            "jira qa ticket:PROJECT-12345\nepic ticket:PROJECT-67890\n"
        )

        # Should fail because labels are case-sensitive
        with pytest.raises(InputFileError):
            parse_atlassian_input(input_file)


class TestFormatTicketOutput:
    """Test format_ticket_output function."""

    def test_format_ticket_output_basic(self):
        """Test basic ticket output formatting."""
        result = format_ticket_output(
            "PROJECT-12345", "Task", "Test summary"
        )

        assert "PROJECT-12345" in result
        assert "Task" in result
        assert "Test summary" in result
        assert "JIRA TICKET SUMMARY" in result
        assert "Issue Key:" in result
        assert "Issue Type:" in result
        assert "Summary:" in result

    def test_format_ticket_output_box_characters(self):
        """Test that output contains box drawing characters."""
        result = format_ticket_output(
            "PROJECT-12345", "Task", "Test summary"
        )

        # Check for box drawing characters
        assert "╔" in result  # Top left
        assert "╗" in result  # Top right
        assert "╚" in result  # Bottom left
        assert "╝" in result  # Bottom right
        assert "║" in result  # Vertical
        assert "═" in result  # Horizontal

    def test_format_ticket_output_long_summary(self):
        """Test formatting with long summary that wraps."""
        long_summary = " ".join(["Word"] * 50)  # Create a long summary
        result = format_ticket_output(
            "PROJECT-12345", "Task", long_summary
        )

        # Should contain the summary (may be wrapped)
        assert "Word" in result
        # Should have multiple lines
        assert result.count("\n") > 5

    def test_format_ticket_output_empty_summary(self):
        """Test formatting with empty summary."""
        result = format_ticket_output("PROJECT-12345", "Task", "")

        assert "PROJECT-12345" in result
        assert "Task" in result
        # Should show placeholder or empty summary
        assert "(No summary available)" in result or "Summary:" in result

    def test_format_ticket_output_special_characters(self):
        """Test formatting with special characters in summary."""
        special_summary = "Test & Summary <with> special chars: 'quotes'"
        result = format_ticket_output(
            "PROJECT-12345", "Task", special_summary
        )

        assert "PROJECT-12345" in result
        assert "Task" in result
        # Should handle special characters gracefully
        assert "Test" in result

    def test_format_ticket_output_custom_width(self):
        """Test formatting with custom width."""
        result_narrow = format_ticket_output(
            "PROJECT-12345", "Task", "Test summary", width=40
        )
        result_wide = format_ticket_output(
            "PROJECT-12345", "Task", "Test summary", width=80
        )

        # Wide output should have longer lines
        first_line_narrow = result_narrow.split("\n")[0]
        first_line_wide = result_wide.split("\n")[0]
        assert len(first_line_wide) > len(first_line_narrow)

    def test_format_ticket_output_width_limits(self):
        """Test that width is constrained to reasonable limits."""
        # Test with very small width (should be clamped to minimum)
        result_small = format_ticket_output(
            "PROJECT-12345", "Task", "Test summary", width=10
        )
        # Should still be readable (minimum width enforced)
        assert len(result_small.split("\n")[0]) >= 40

        # Test with very large width (should be clamped to maximum)
        result_large = format_ticket_output(
            "PROJECT-12345", "Task", "Test summary", width=200
        )
        # Should not exceed maximum width
        assert len(result_large.split("\n")[0]) <= 100

    def test_format_ticket_output_structure(self):
        """Test that output has correct structure."""
        result = format_ticket_output(
            "PROJECT-12345", "Task", "Test summary"
        )

        lines = result.split("\n")
        # Should have at least: top border, header, separator, key, type, summary, bottom border
        assert len(lines) >= 6

        # First line should be top border
        assert lines[0].startswith("╔")
        assert lines[0].endswith("╗")

        # Last line should be bottom border
        assert lines[-1].startswith("╚")
        assert lines[-1].endswith("╝")

