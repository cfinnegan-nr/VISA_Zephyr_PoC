"""
Utility functions for JIRA Ticket Reader application.

This module provides helper functions for parsing input files,
formatting output, and other utility operations.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from src.exceptions import InputFileError

# Configure logging for this module
logger = logging.getLogger(__name__)


def parse_atlassian_input(input_file_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Parse the AtlassianInput.txt file to extract JIRA ticket keys.

    This function reads the AtlassianInput.txt file from the project root
    and extracts the JIRA QA Ticket and EPIC Ticket keys. The file format
    is expected to be:
        JIRA QA Ticket:PROJECT-XXXXX
        EPIC Ticket:PROJECT-XXXXX

    Args:
        input_file_path: Optional path to the input file. If not provided,
            defaults to AtlassianInput.txt in the project root.

    Returns:
        Dictionary with keys 'qa_ticket' and 'epic_ticket' containing
        the respective JIRA ticket keys.

    Raises:
        InputFileError: If the file cannot be read, is missing required
            ticket keys, or has an invalid format.

    Example:
        >>> tickets = parse_atlassian_input()
        >>> print(tickets['qa_ticket'])
        PROJECT-12345
        >>> print(tickets['epic_ticket'])
        PROJECT-67890
    """
    # Default to project root if path not provided
    if input_file_path is None:
        # Get project root (parent of src directory)
        project_root = Path(__file__).parent.parent
        input_file_path = project_root / "AtlassianInput.txt"

    logger.info(f"Reading input file: {input_file_path}")

    try:
        # Check if file exists
        if not input_file_path.exists():
            raise InputFileError(
                f"Input file not found: {input_file_path}\n"
                "Please create AtlassianInput.txt in the project root.\n"
                "You can copy AtlassianInput.example.txt as a template."
            )

        # Read file contents
        try:
            with open(input_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except IOError as e:
            raise InputFileError(
                f"Failed to read input file {input_file_path}: {e}"
            ) from e

        # Parse lines to extract ticket keys
        qa_ticket: Optional[str] = None
        epic_ticket: Optional[str] = None

        for line_num, line in enumerate(lines, start=1):
            # Strip whitespace and skip empty lines
            line = line.strip()
            if not line:
                continue

            # Parse JIRA QA Ticket line
            if line.startswith("JIRA QA Ticket:"):
                # Extract ticket key after the colon
                parts = line.split(":", 1)
                if len(parts) == 2:
                    qa_ticket = parts[1].strip()
                    logger.debug(f"Found QA ticket: {qa_ticket}")
                else:
                    logger.warning(
                        f"Invalid format on line {line_num}: {line}. "
                        "Expected format: JIRA QA Ticket:INVHUB-XXXXX"
                    )

            # Parse EPIC Ticket line
            elif line.startswith("EPIC Ticket:"):
                # Extract ticket key after the colon
                parts = line.split(":", 1)
                if len(parts) == 2:
                    epic_ticket = parts[1].strip()
                    logger.debug(f"Found Epic ticket: {epic_ticket}")
                else:
                    logger.warning(
                        f"Invalid format on line {line_num}: {line}. "
                        "Expected format: EPIC Ticket:INVHUB-XXXXX"
                    )

        # Validate that both tickets were found
        if not qa_ticket:
            raise InputFileError(
                "QA Ticket key not found in input file. "
                "Expected line: JIRA QA Ticket:INVHUB-XXXXX"
            )

        if not epic_ticket:
            raise InputFileError(
                "EPIC Ticket key not found in input file. "
                "Expected line: EPIC Ticket:INVHUB-XXXXX"
            )

        # Validate ticket key format (basic check)
        if not qa_ticket or len(qa_ticket) < 3:
            raise InputFileError(
                f"Invalid QA ticket key format: {qa_ticket}. "
                "Expected format: PROJECT-XXXXX"
            )

        if not epic_ticket or len(epic_ticket) < 3:
            raise InputFileError(
                f"Invalid Epic ticket key format: {epic_ticket}. "
                "Expected format: PROJECT-XXXXX"
            )

        logger.info(
            f"Successfully parsed tickets - QA: {qa_ticket}, Epic: {epic_ticket}"
        )

        return {
            "qa_ticket": qa_ticket,
            "epic_ticket": epic_ticket,
        }

    except InputFileError:
        # Re-raise InputFileError as-is
        raise
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error parsing input file: {e}", exc_info=True)
        raise InputFileError(
            f"Failed to parse input file: {e}"
        ) from e


def format_ticket_output(
    issue_key: str, issue_type: str, summary: str, width: int = 60
) -> str:
    """
    Format JIRA ticket information into an aesthetically pleasing output.

    This function creates a formatted box with borders and proper spacing
    to display JIRA ticket information in a user-friendly way.

    Args:
        issue_key: The JIRA issue key (e.g., INVHUB-21868).
        issue_type: The issue type name (e.g., "QA Ticket", "Epic").
        summary: The ticket summary text.
        width: The width of the output box in characters. Defaults to 60.

    Returns:
        Formatted string containing the ticket information in a box format.

    Example:
        >>> output = format_ticket_output(
        ...     "INVHUB-21868", "QA Ticket", "Test ticket summary"
        ... )
        >>> print(output)
    """
    # Ensure width is reasonable (minimum 40, maximum 100)
    width = max(40, min(100, width))

    # Box drawing characters for borders
    top_left = "╔"
    top_right = "╗"
    bottom_left = "╚"
    bottom_right = "╝"
    horizontal = "═"
    vertical = "║"
    left_tee = "╠"
    right_tee = "╣"
    horizontal_line = "─"

    # Create header line
    header = "JIRA TICKET SUMMARY"
    header_padding = (width - len(header) - 2) // 2
    header_line = (
        f"{vertical} {header:^{width-4}} {vertical}"
    )

    # Create top border
    top_border = top_left + horizontal * (width - 2) + top_right

    # Create separator line
    separator = left_tee + horizontal * (width - 2) + right_tee

    # Format issue key line
    issue_key_label = "Issue Key:"
    issue_key_line = (
        f"{vertical} {issue_key_label:<15} {issue_key:<{width-20}} {vertical}"
    )

    # Format issue type line
    issue_type_label = "Issue Type:"
    issue_type_line = (
        f"{vertical} {issue_type_label:<15} {issue_type:<{width-20}} {vertical}"
    )

    # Format summary line(s)
    # Word wrap summary if it's too long
    summary_label = "Summary:"
    summary_text = summary or "(No summary available)"
    summary_lines = []

    # Split summary into words and wrap to fit available width
    words = summary_text.split()
    current_line = ""
    available_width = width - 22  # Account for borders and label

    for word in words:
        # Check if adding this word would exceed the line width
        test_line = f"{current_line} {word}".strip() if current_line else word
        if len(test_line) <= available_width:
            current_line = test_line
        else:
            # Current line is full, add it and start a new one
            if current_line:
                summary_lines.append(
                    f"{vertical} {summary_label:<15} "
                    f"{current_line:<{available_width}} {vertical}"
                )
                summary_label = ""  # Only show label on first line
            current_line = word

    # Add the last line if there's content
    if current_line:
        summary_lines.append(
            f"{vertical} {summary_label:<15} "
            f"{current_line:<{available_width}} {vertical}"
        )

    # If summary was empty, add a placeholder line
    if not summary_lines:
        summary_lines.append(
            f"{vertical} {summary_label:<15} "
            f"{'(No summary available)':<{available_width}} {vertical}"
        )

    # Create bottom border
    bottom_border = bottom_left + horizontal * (width - 2) + bottom_right

    # Combine all parts
    output_lines = [
        top_border,
        header_line,
        separator,
        issue_key_line,
        issue_type_line,
    ]
    output_lines.extend(summary_lines)
    output_lines.append(bottom_border)

    return "\n".join(output_lines)

