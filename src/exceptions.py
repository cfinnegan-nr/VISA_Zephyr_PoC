"""
Custom exception classes for the JIRA Ticket Reader application.

This module defines custom exceptions used throughout the application
to provide more specific error handling and clearer error messages.
"""


class JiraReaderError(Exception):
    """Base exception class for all JIRA Reader errors."""

    pass


class JiraConnectionError(JiraReaderError):
    """Raised when there are network or connection issues with JIRA."""

    pass


class JiraAuthenticationError(JiraReaderError):
    """Raised when JIRA authentication fails (401, 403 errors)."""

    pass


class JiraIssueNotFoundError(JiraReaderError):
    """Raised when a JIRA issue cannot be found (404 error)."""

    pass


class JiraConfigurationError(JiraReaderError):
    """Raised when JIRA configuration is missing or invalid."""

    pass


class InputFileError(JiraReaderError):
    """Raised when there are errors reading or parsing the input file."""

    pass

