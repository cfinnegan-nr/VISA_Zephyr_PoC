"""
JIRA Ticket Reader main application module.

This module provides the main application logic and JIRA API client
for fetching ticket information from an Atlassian JIRA instance.
"""

import base64
import logging
from typing import Dict, Optional

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import (
    ConnectionError,
    HTTPError,
    RequestException,
    Timeout,
)

from src.config import Settings, load_settings
from src.exceptions import (
    JiraAuthenticationError,
    JiraConnectionError,
    JiraConfigurationError,
    JiraIssueNotFoundError,
)
from src.utils import format_ticket_output, parse_atlassian_input

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class JiraClient:
    """
    Client for interacting with JIRA REST API.

    This class provides methods to fetch JIRA issue information
    using the JIRA REST API v3. It handles authentication, error
    handling, and response parsing.

    Attributes:
        server_url: Base URL of the JIRA instance.
        username: JIRA username for authentication.
        api_token: JIRA API token for authentication.
        session: Requests session object for making API calls.

    Example:
        >>> client = JiraClient(settings)
        >>> issue = client.get_issue("INVHUB-21868")
        >>> print(issue['summary'])
    """

    def __init__(self, settings: Settings):
        """
        Initialize JIRA client with settings.

        Args:
            settings: Settings object containing JIRA credentials.

        Raises:
            JiraConfigurationError: If settings are invalid.
        """
        try:
            # Store configuration
            self.server_url = settings.jira_server_url.rstrip("/")
            self.username = settings.jira_username
            self.api_token = settings.jira_api_token

            # Validate server URL format
            if not self.server_url.startswith(("http://", "https://")):
                raise JiraConfigurationError(
                    f"Invalid JIRA server URL format: {self.server_url}"
                )

            # Create a requests session for connection pooling
            self.session = requests.Session()

            # Set up Basic Authentication
            # SECURITY: Never log the API token!
            self.session.auth = HTTPBasicAuth(self.username, self.api_token)

            # Set default headers
            self.session.headers.update(
                {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }
            )

            logger.info(f"Initialized JIRA client for server: {self.server_url}")

        except Exception as e:
            logger.error(f"Failed to initialize JIRA client: {e}", exc_info=True)
            raise JiraConfigurationError(
                f"Failed to initialize JIRA client: {e}"
            ) from e

    def get_issue(self, issue_key: str) -> Dict[str, str]:
        """
        Fetch a JIRA issue by its key.

        This method makes a GET request to the JIRA REST API to retrieve
        issue information including summary and issue type.

        Args:
            issue_key: The JIRA issue key (e.g., "INVHUB-21868").

        Returns:
            Dictionary containing:
                - 'key': Issue key
                - 'summary': Issue summary
                - 'issue_type': Issue type name

        Raises:
            JiraConnectionError: If there's a network or connection error.
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraIssueNotFoundError: If the issue is not found (404).
            RequestException: For other HTTP errors.

        Example:
            >>> client = JiraClient(settings)
            >>> issue = client.get_issue("INVHUB-21868")
            >>> print(f"Issue: {issue['key']} - {issue['summary']}")
        """
        # Construct API URL
        # JIRA REST API v3 endpoint for getting an issue
        api_url = f"{self.server_url}/rest/api/3/issue/{issue_key}"

        logger.info(f"Fetching issue: {issue_key} from {self.server_url}")

        try:
            # Make GET request to JIRA API
            # Request only the fields we need: summary and issuetype
            params = {
                "fields": "summary,issuetype",
            }

            response = self.session.get(api_url, params=params, timeout=30)

            # Check for HTTP errors
            response.raise_for_status()

            # Parse JSON response
            try:
                issue_data = response.json()
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise JiraConnectionError(
                    f"Invalid response from JIRA API for issue {issue_key}"
                ) from e

            # Extract required information
            # Handle nested structure: issue_data['fields']['summary']
            summary = issue_data.get("fields", {}).get("summary", "")
            issue_type_data = issue_data.get("fields", {}).get("issuetype", {})
            issue_type_name = issue_type_data.get("name", "Unknown")

            logger.info(
                f"Successfully fetched issue {issue_key}: "
                f"{issue_type_name} - {summary[:50]}..."
            )

            return {
                "key": issue_key,
                "summary": summary,
                "issue_type": issue_type_name,
            }

        except Timeout as e:
            # Request timed out
            logger.error(f"Request timeout while fetching issue {issue_key}: {e}")
            raise JiraConnectionError(
                f"Request to JIRA timed out. Please check your network "
                f"connection and try again."
            ) from e

        except ConnectionError as e:
            # Network connection error
            logger.error(
                f"Connection error while fetching issue {issue_key}: {e}"
            )
            raise JiraConnectionError(
                f"Failed to connect to JIRA server at {self.server_url}. "
                f"Please check your network connection and server URL."
            ) from e

        except HTTPError as e:
            # HTTP error (4xx, 5xx)
            status_code = e.response.status_code if e.response else 0

            if status_code == 401:
                # Unauthorized - authentication failed
                logger.error(f"Authentication failed for issue {issue_key}: {e}")
                raise JiraAuthenticationError(
                    "JIRA authentication failed. Please check your "
                    "JIRA_USERNAME and JIRA_API_TOKEN credentials."
                ) from e

            elif status_code == 403:
                # Forbidden - no permission
                logger.error(f"Access forbidden for issue {issue_key}: {e}")
                raise JiraAuthenticationError(
                    f"You do not have permission to access issue {issue_key}. "
                    "Please check your JIRA permissions."
                ) from e

            elif status_code == 404:
                # Not found
                logger.warning(f"Issue not found: {issue_key}")
                raise JiraIssueNotFoundError(
                    f"JIRA issue {issue_key} not found. "
                    "Please verify the issue key is correct."
                ) from e

            else:
                # Other HTTP errors
                logger.error(
                    f"HTTP error {status_code} while fetching issue {issue_key}: {e}"
                )
                raise JiraConnectionError(
                    f"JIRA API returned error {status_code} for issue {issue_key}. "
                    f"Response: {e.response.text if e.response else 'No response'}"
                ) from e

        except RequestException as e:
            # Other request-related errors
            logger.error(
                f"Request error while fetching issue {issue_key}: {e}",
                exc_info=True,
            )
            raise JiraConnectionError(
                f"Failed to fetch issue {issue_key}: {e}"
            ) from e

        except Exception as e:
            # Catch any other unexpected errors
            logger.error(
                f"Unexpected error while fetching issue {issue_key}: {e}",
                exc_info=True,
            )
            raise JiraConnectionError(
                f"Unexpected error fetching issue {issue_key}: {e}"
            ) from e

    def close(self):
        """
        Close the requests session.

        This method should be called when done with the client
        to properly clean up resources.
        """
        if hasattr(self, "session"):
            self.session.close()
            logger.debug("JIRA client session closed")


def main():
    """
    Main application entry point.

    This function orchestrates the entire workflow:
    1. Load configuration from environment variables
    2. Parse input file to get ticket keys
    3. Initialize JIRA client
    4. Fetch ticket information
    5. Format and display results

    All errors are caught and displayed with user-friendly messages.
    """
    client: Optional[JiraClient] = None

    try:
        # Step 1: Load configuration
        logger.info("Loading JIRA configuration...")
        try:
            settings = load_settings()
        except JiraConfigurationError as e:
            print("\n" + "=" * 70)
            print("ERROR: Configuration Error")
            print("=" * 70)
            print(str(e))
            print("\nPlease create a .env file in the project root with:")
            print("  JIRA_SERVER_URL=https://your-instance.atlassian.net")
            print("  JIRA_USERNAME=your-email@example.com")
            print("  JIRA_API_TOKEN=your-api-token")
            print("\nSee .env.example for a template.")
            print("=" * 70 + "\n")
            return 1

        # Step 2: Parse input file
        logger.info("Parsing input file...")
        try:
            tickets = parse_atlassian_input()
            qa_ticket_key = tickets["qa_ticket"]
            epic_ticket_key = tickets["epic_ticket"]
        except Exception as e:
            print("\n" + "=" * 70)
            print("ERROR: Failed to parse input file")
            print("=" * 70)
            print(str(e))
            print("=" * 70 + "\n")
            return 1

        # Step 3: Initialize JIRA client
        logger.info("Initializing JIRA client...")
        try:
            client = JiraClient(settings)
        except Exception as e:
            print("\n" + "=" * 70)
            print("ERROR: Failed to initialize JIRA client")
            print("=" * 70)
            print(str(e))
            print("=" * 70 + "\n")
            return 1

        # Step 4 & 5: Fetch and display tickets
        print("\n" + "=" * 70)
        print("Fetching JIRA Ticket Information")
        print("=" * 70 + "\n")

        # Fetch QA ticket
        try:
            logger.info(f"Fetching QA ticket: {qa_ticket_key}")
            qa_ticket = client.get_issue(qa_ticket_key)
            print(format_ticket_output(
                qa_ticket["key"],
                qa_ticket["issue_type"],
                qa_ticket["summary"],
            ))
            print()  # Add blank line between tickets
        except JiraIssueNotFoundError as e:
            print(f"WARNING: {e}")
            print()
        except Exception as e:
            print(f"ERROR fetching QA ticket {qa_ticket_key}: {e}")
            print()

        # Fetch Epic ticket
        try:
            logger.info(f"Fetching Epic ticket: {epic_ticket_key}")
            epic_ticket = client.get_issue(epic_ticket_key)
            print(format_ticket_output(
                epic_ticket["key"],
                epic_ticket["issue_type"],
                epic_ticket["summary"],
            ))
            print()  # Add blank line at end
        except JiraIssueNotFoundError as e:
            print(f"WARNING: {e}")
            print()
        except Exception as e:
            print(f"ERROR fetching Epic ticket {epic_ticket_key}: {e}")
            print()

        logger.info("Application completed successfully")
        return 0

    except KeyboardInterrupt:
        # Handle user interruption (Ctrl+C)
        print("\n\nOperation cancelled by user.")
        logger.info("Application interrupted by user")
        return 130

    except Exception as e:
        # Catch any other unexpected errors
        print("\n" + "=" * 70)
        print("ERROR: Unexpected error occurred")
        print("=" * 70)
        print(str(e))
        print("=" * 70 + "\n")
        logger.error(f"Unexpected error in main: {e}", exc_info=True)
        return 1

    finally:
        # Clean up resources
        if client:
            try:
                client.close()
            except Exception as e:
                logger.warning(f"Error closing JIRA client: {e}")


if __name__ == "__main__":
    exit(main())

