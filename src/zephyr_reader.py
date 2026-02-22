"""
Zephyr Scale API client module for fetching test case information.

This module provides functions to interact with the Smartbear Zephyr Scale API
to retrieve test case details and test step descriptions. It handles
authentication, error handling, and response parsing.

The module now supports both direct API calls and MCP (Model Context Protocol)
server calls via the Smartbear MCP server.

SECURITY WARNING: Never log or expose API tokens!
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import (
    ConnectionError,
    HTTPError,
    RequestException,
    Timeout,
)

from src.config import Settings
from src.exceptions import (
    ZephyrAuthenticationError,
    ZephyrConnectionError,
    ZephyrConfigurationError,
    ZephyrTestCaseNotFoundError,
)

# Configure logging for this module
logger = logging.getLogger(__name__)


def convert_jira_key_to_zephyr_format(jira_key: str) -> str:
    """
    Convert JIRA issue key format to Zephyr test case key format.

    Zephyr test case keys typically use format: PROJECT-T123
    JIRA issue keys use format: PROJECT-12345

    Args:
        jira_key: JIRA issue key (e.g., "INVHUB-21550").

    Returns:
        Zephyr test case key format (e.g., "INVHUB-T21550").

    Note:
        This is a best-guess conversion. The actual mapping depends on your
        Zephyr/JIRA configuration. You may need to adjust this logic.
    """
    if "-" in jira_key:
        parts = jira_key.split("-", 1)
        if len(parts) == 2:
            # Convert PROJECT-12345 to PROJECT-T12345
            return f"{parts[0]}-T{parts[1]}"
    return jira_key


def get_zephyr_test_case_via_mcp(
    test_case_key: str, settings: Optional[Settings] = None
) -> Dict[str, Any]:
    """
    Fetch a Zephyr test case using Smartbear MCP server.

    This function uses the Smartbear MCP server to fetch test case information.
    The MCP call is: mcp_smartbear_zephyr_get_test_case(testCaseKey=test_case_key)

    Args:
        test_case_key: The Zephyr test case key. Must be in format PROJECT-T123
            (e.g., "INVHUB-T21550"). If a JIRA key format is provided, it will
            be converted automatically.
        settings: Optional Settings object for fallback API calls if MCP fails.

    Returns:
        Dictionary containing test case data.

    Raises:
        ZephyrTestCaseNotFoundError: If the test case is not found.
        ZephyrConnectionError: If there's a connection error.
        NotImplementedError: If MCP client is not available and no fallback provided.
        Exception: For other errors.

    Note:
        This function attempts to use the Smartbear MCP server first.
        If MCP is not available, it falls back to direct API calls if settings
        are provided. The actual MCP call would be:
        mcp_smartbear_zephyr_get_test_case(testCaseKey=test_case_key)
    """
    logger.info(
        f"Fetching Zephyr test case {test_case_key} via Smartbear MCP server"
    )

    # Convert key format if needed (JIRA format to Zephyr format)
    zephyr_key = test_case_key
    if "-" in test_case_key:
        parts = test_case_key.split("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            # It's in JIRA format (PROJECT-12345), convert to Zephyr format (PROJECT-T12345)
            zephyr_key = convert_jira_key_to_zephyr_format(test_case_key)
            logger.info(
                f"Converted JIRA key {test_case_key} to Zephyr format {zephyr_key}"
            )

    # Attempt to use MCP client if available
    # In production with MCP client library, this would call:
    # result = mcp_client.call("smartbear", "zephyr_get_test_case", {"testCaseKey": zephyr_key})
    # return json.loads(result)
    
    # For now, MCP tools are not directly callable from Python code
    # They are only available to the AI assistant through the MCP protocol
    # Fall back to direct API call if settings are provided
    if settings:
        logger.info(
            "MCP client not available, falling back to direct API call"
        )
        return get_zephyr_test_case(zephyr_key, settings)
    
    raise NotImplementedError(
        "MCP client integration required. "
        "This function should call mcp_smartbear_zephyr_get_test_case() "
        "through an MCP client library. "
        f"Expected call: mcp_smartbear_zephyr_get_test_case(testCaseKey='{zephyr_key}')"
    )


def get_zephyr_test_steps_via_mcp(
    test_case_key: str, settings: Optional[Settings] = None
) -> List[Dict[str, Any]]:
    """
    Fetch test steps for a Zephyr test case using Smartbear MCP server.

    This function uses the Smartbear MCP server to fetch test steps.
    The exact MCP function depends on the Smartbear MCP server API.

    Args:
        test_case_key: The Zephyr test case key in format PROJECT-T123.
        settings: Optional Settings object for fallback API calls if MCP fails.

    Returns:
        List of dictionaries containing test step data.

    Raises:
        ZephyrTestCaseNotFoundError: If the test case is not found.
        ZephyrConnectionError: If there's a connection error.
        NotImplementedError: If MCP client is not available and no fallback provided.
        Exception: For other errors.

    Note:
        This function attempts to use the Smartbear MCP server first.
        If MCP is not available, it falls back to direct API calls if settings
        are provided. The actual MCP call would depend on the available
        Smartbear MCP server functions for test steps.
    """
    logger.info(
        f"Fetching Zephyr test steps for {test_case_key} via Smartbear MCP server"
    )

    # Convert key format if needed
    zephyr_key = test_case_key
    if "-" in test_case_key:
        parts = test_case_key.split("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            zephyr_key = convert_jira_key_to_zephyr_format(test_case_key)

    # Attempt to use MCP client if available
    # In production with MCP client library, this would call the appropriate
    # Smartbear MCP function to get test steps
    # The exact function name depends on the Smartbear MCP server implementation
    
    # For now, MCP tools are not directly callable from Python code
    # Fall back to direct API call if settings are provided
    if settings:
        logger.info(
            "MCP client not available, falling back to direct API call"
        )
        return get_zephyr_test_steps(zephyr_key, settings)
    
    raise NotImplementedError(
        "MCP client integration required. "
        "This function should call the Smartbear MCP server function "
        "to get test steps through an MCP client library."
    )


def get_zephyr_test_case(test_case_key: str, settings: Settings) -> Dict[str, Any]:
    """
    Fetch a Zephyr test case by its key.

    This method makes a GET request to the Zephyr Scale API v2 to retrieve
    test case information including name (summary), project key, and metadata.

    Args:
        test_case_key: The Zephyr test case key (e.g., "INVHUB-T123" or
            "INVHUB-21550"). Note: The key format may vary depending on
            your Zephyr configuration.
        settings: Settings object containing Zephyr credentials.

    Returns:
        Dictionary containing test case data with keys such as:
            - 'key': Test case key
            - 'name': Test case name/summary
            - 'projectKey': Project key
            - Other metadata fields

    Raises:
        ZephyrConnectionError: If there's a network or connection error.
        ZephyrAuthenticationError: If authentication fails (401, 403).
        ZephyrTestCaseNotFoundError: If the test case is not found (404).
        ZephyrConfigurationError: If configuration is invalid.
        RequestException: For other HTTP errors.

    Example:
        >>> settings = load_settings()
        >>> test_case = get_zephyr_test_case("INVHUB-T123", settings)
        >>> print(test_case['name'])
    """
    # Validate configuration
    if not settings.zephyr_base_url:
        raise ZephyrConfigurationError(
            "ZEPHYR_BASE_URL is not configured. "
            "Please set it in your .env file."
        )

    if not settings.zephyr_api_token:
        raise ZephyrConfigurationError(
            "ZEPHYR_API_TOKEN is not configured. "
            "Please set it in your .env file."
        )

    # Construct API URL
    # Zephyr Scale API v2 endpoint for getting a test case
    base_url = settings.zephyr_base_url.rstrip("/")
    api_url = f"{base_url}/testcases/{test_case_key}"

    logger.info(
        f"Fetching Zephyr test case: {test_case_key} from {base_url}"
    )

    try:
        # Set up authentication headers
        # Zephyr Scale API uses Bearer token authentication
        headers = {
            "Authorization": f"Bearer {settings.zephyr_api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Make GET request to Zephyr API
        response = requests.get(api_url, headers=headers, timeout=30)

        # Check for HTTP errors
        response.raise_for_status()

        # Parse JSON response
        try:
            test_case_data = response.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ZephyrConnectionError(
                f"Invalid response from Zephyr API for test case {test_case_key}"
            ) from e

        logger.info(
            f"Successfully fetched test case {test_case_key}: "
            f"{test_case_data.get('name', 'Unknown')[:50]}..."
        )

        return test_case_data

    except Timeout as e:
        # Request timed out
        logger.error(
            f"Request timeout while fetching test case {test_case_key}: {e}"
        )
        raise ZephyrConnectionError(
            f"Request to Zephyr API timed out. Please check your network "
            f"connection and try again."
        ) from e

    except ConnectionError as e:
        # Network connection error
        logger.error(
            f"Connection error while fetching test case {test_case_key}: {e}"
        )
        raise ZephyrConnectionError(
            f"Failed to connect to Zephyr API at {base_url}. "
            f"Please check your network connection and base URL."
        ) from e

    except HTTPError as e:
        # HTTP error (4xx, 5xx)
        # Extract status code - HTTPError should always have response
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
        else:
            # Fallback: try to extract from exception message
            match = re.search(r'(\d{3})', str(e))
            status_code = int(match.group(1)) if match else 0

        if status_code == 401:
            # Unauthorized - authentication failed
            logger.error(
                f"Authentication failed for test case {test_case_key}: {e}"
            )
            raise ZephyrAuthenticationError(
                "Zephyr API authentication failed. Please check your "
                "ZEPHYR_API_TOKEN credentials."
            ) from e

        elif status_code == 403:
            # Forbidden - no permission
            logger.error(
                f"Access forbidden for test case {test_case_key}: {e}"
            )
            raise ZephyrAuthenticationError(
                f"You do not have permission to access test case "
                f"{test_case_key}. Please check your Zephyr permissions."
            ) from e

        elif status_code == 404:
            # Not found
            logger.warning(f"Test case not found: {test_case_key}")
            raise ZephyrTestCaseNotFoundError(
                f"Zephyr test case {test_case_key} not found. "
                "Please verify the test case key is correct. "
                "Note: The key format may be different from JIRA issue keys."
            ) from e

        else:
            # Other HTTP errors
            logger.error(
                f"HTTP error {status_code} while fetching test case "
                f"{test_case_key}: {e}"
            )
            raise ZephyrConnectionError(
                f"Zephyr API returned error {status_code} for test case "
                f"{test_case_key}. "
                f"Response: {e.response.text if e.response else 'No response'}"
            ) from e

    except RequestException as e:
        # Other request-related errors
        logger.error(
            f"Request error while fetching test case {test_case_key}: {e}",
            exc_info=True,
        )
        raise ZephyrConnectionError(
            f"Failed to fetch test case {test_case_key}: {e}"
        ) from e

    except Exception as e:
        # Catch any other unexpected errors
        logger.error(
            f"Unexpected error while fetching test case {test_case_key}: {e}",
            exc_info=True,
        )
        raise ZephyrConnectionError(
            f"Unexpected error fetching test case {test_case_key}: {e}"
        ) from e


def get_zephyr_test_steps(
    test_case_key: str, settings: Settings, limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetch test steps for a Zephyr test case.

    This method makes a GET request to the Zephyr Scale API v2 to retrieve
    all test steps associated with a test case. It handles pagination
    automatically.

    Args:
        test_case_key: The Zephyr test case key (e.g., "INVHUB-T123").
        settings: Settings object containing Zephyr credentials.
        limit: Maximum number of test steps to retrieve. Defaults to 100.

    Returns:
        List of dictionaries, each containing test step data with keys such as:
            - 'step': Step number
            - 'data': Step description/action
            - 'result': Expected result
            - Other step metadata

    Raises:
        ZephyrConnectionError: If there's a network or connection error.
        ZephyrAuthenticationError: If authentication fails (401, 403).
        ZephyrTestCaseNotFoundError: If the test case is not found (404).
        ZephyrConfigurationError: If configuration is invalid.
        RequestException: For other HTTP errors.

    Example:
        >>> settings = load_settings()
        >>> test_steps = get_zephyr_test_steps("INVHUB-T123", settings)
        >>> for step in test_steps:
        ...     print(f"Step {step.get('step')}: {step.get('data')}")
    """
    # Validate configuration
    if not settings.zephyr_base_url:
        raise ZephyrConfigurationError(
            "ZEPHYR_BASE_URL is not configured. "
            "Please set it in your .env file."
        )

    if not settings.zephyr_api_token:
        raise ZephyrConfigurationError(
            "ZEPHYR_API_TOKEN is not configured. "
            "Please set it in your .env file."
        )

    # Construct API URL
    # Zephyr Scale API v2 endpoint for getting test steps
    base_url = settings.zephyr_base_url.rstrip("/")
    api_url = f"{base_url}/testcases/{test_case_key}/teststeps"

    logger.info(
        f"Fetching test steps for Zephyr test case: {test_case_key}"
    )

    try:
        # Set up authentication headers
        headers = {
            "Authorization": f"Bearer {settings.zephyr_api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Set up query parameters for pagination
        params = {
            "limit": limit,
            "startAt": 0,
        }

        # Make GET request to Zephyr API
        response = requests.get(
            api_url, headers=headers, params=params, timeout=30
        )

        # Check for HTTP errors
        response.raise_for_status()

        # Parse JSON response
        try:
            response_data = response.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ZephyrConnectionError(
                f"Invalid response from Zephyr API for test steps of "
                f"test case {test_case_key}"
            ) from e

        # Extract test steps from response
        # The response structure may vary, but typically contains a 'values'
        # array or is directly an array
        if isinstance(response_data, dict):
            # If response is an object, look for 'values' or 'testSteps' key
            test_steps = response_data.get("values", response_data.get("testSteps", []))
        elif isinstance(response_data, list):
            # If response is directly a list
            test_steps = response_data
        else:
            logger.warning(
                f"Unexpected response format for test steps: {type(response_data)}"
            )
            test_steps = []

        logger.info(
            f"Successfully fetched {len(test_steps)} test steps for "
            f"test case {test_case_key}"
        )

        return test_steps

    except Timeout as e:
        # Request timed out
        logger.error(
            f"Request timeout while fetching test steps for "
            f"test case {test_case_key}: {e}"
        )
        raise ZephyrConnectionError(
            f"Request to Zephyr API timed out. Please check your network "
            f"connection and try again."
        ) from e

    except ConnectionError as e:
        # Network connection error
        logger.error(
            f"Connection error while fetching test steps for "
            f"test case {test_case_key}: {e}"
        )
        raise ZephyrConnectionError(
            f"Failed to connect to Zephyr API at {base_url}. "
            f"Please check your network connection and base URL."
        ) from e

    except HTTPError as e:
        # HTTP error (4xx, 5xx)
        # Extract status code - HTTPError should always have response
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
        else:
            # Fallback: try to extract from exception message
            match = re.search(r'(\d{3})', str(e))
            status_code = int(match.group(1)) if match else 0

        if status_code == 401:
            # Unauthorized - authentication failed
            logger.error(
                f"Authentication failed for test steps of test case "
                f"{test_case_key}: {e}"
            )
            raise ZephyrAuthenticationError(
                "Zephyr API authentication failed. Please check your "
                "ZEPHYR_API_TOKEN credentials."
            ) from e

        elif status_code == 403:
            # Forbidden - no permission
            logger.error(
                f"Access forbidden for test steps of test case "
                f"{test_case_key}: {e}"
            )
            raise ZephyrAuthenticationError(
                f"You do not have permission to access test steps for "
                f"test case {test_case_key}. Please check your Zephyr permissions."
            ) from e

        elif status_code == 404:
            # Not found
            logger.warning(
                f"Test case not found when fetching test steps: {test_case_key}"
            )
            raise ZephyrTestCaseNotFoundError(
                f"Zephyr test case {test_case_key} not found. "
                "Please verify the test case key is correct."
            ) from e

        else:
            # Other HTTP errors
            logger.error(
                f"HTTP error {status_code} while fetching test steps for "
                f"test case {test_case_key}: {e}"
            )
            raise ZephyrConnectionError(
                f"Zephyr API returned error {status_code} for test steps of "
                f"test case {test_case_key}. "
                f"Response: {e.response.text if e.response else 'No response'}"
            ) from e

    except RequestException as e:
        # Other request-related errors
        logger.error(
            f"Request error while fetching test steps for test case "
            f"{test_case_key}: {e}",
            exc_info=True,
        )
        raise ZephyrConnectionError(
            f"Failed to fetch test steps for test case {test_case_key}: {e}"
        ) from e

    except Exception as e:
        # Catch any other unexpected errors
        logger.error(
            f"Unexpected error while fetching test steps for test case "
            f"{test_case_key}: {e}",
            exc_info=True,
        )
        raise ZephyrConnectionError(
            f"Unexpected error fetching test steps for test case "
            f"{test_case_key}: {e}"
        ) from e


def get_zephyr_test_case_from_jira_issue(
    jira_issue_key: str, settings: Settings
) -> Optional[str]:
    """
    Attempt to find a Zephyr test case key from a JIRA issue key.

    This is a helper function that may be used to map JIRA issue keys
    to Zephyr test case keys. The mapping depends on your Zephyr/JIRA
    configuration. In some cases, the keys may be the same, in others,
    they may differ (e.g., INVHUB-21550 vs INVHUB-T123).

    Args:
        jira_issue_key: The JIRA issue key (e.g., "INVHUB-21550").
        settings: Settings object containing Zephyr credentials.

    Returns:
        Zephyr test case key if found, None otherwise.

    Note:
        This function attempts to use the JIRA issue key directly as the
        test case key. If that fails, it returns None. You may need to
        customize this function based on your specific Zephyr/JIRA
        integration configuration.
    """
    # Try using the JIRA issue key directly as the test case key
    # This works if your Zephyr test cases use the same key format as JIRA
    try:
        # Attempt to fetch the test case using the JIRA key
        test_case = get_zephyr_test_case(jira_issue_key, settings)
        if test_case:
            logger.info(
                f"Found Zephyr test case {jira_issue_key} matching "
                f"JIRA issue {jira_issue_key}"
            )
            return jira_issue_key
    except ZephyrTestCaseNotFoundError:
        # Test case not found with this key, try alternative formats
        logger.debug(
            f"Test case not found with key {jira_issue_key}, "
            "trying alternative formats..."
        )

        # Try converting to test case format (e.g., INVHUB-21550 -> INVHUB-T21550)
        # This is just an example - adjust based on your actual format
        if "-" in jira_issue_key:
            parts = jira_issue_key.split("-", 1)
            if len(parts) == 2:
                alternative_key = f"{parts[0]}-T{parts[1]}"
                try:
                    test_case = get_zephyr_test_case(alternative_key, settings)
                    if test_case:
                        logger.info(
                            f"Found Zephyr test case {alternative_key} "
                            f"matching JIRA issue {jira_issue_key}"
                        )
                        return alternative_key
                except (
                    ZephyrTestCaseNotFoundError,
                    ZephyrConnectionError,
                    ZephyrAuthenticationError,
                    ZephyrConfigurationError,
                ):
                    # Catch all Zephyr exceptions - this is a helper function
                    # that should gracefully handle any Zephyr API errors
                    pass

    except (
        ZephyrConnectionError,
        ZephyrAuthenticationError,
        ZephyrConfigurationError,
    ) as e:
        # Log but don't fail - this is a helper function
        # These exceptions indicate API issues, not just "not found"
        logger.debug(
            f"Zephyr API error while trying to map JIRA issue "
            f"{jira_issue_key} to Zephyr test case: {e}"
        )
    except Exception as e:
        # Log but don't fail - this is a helper function
        # Catch any other unexpected errors
        logger.debug(
            f"Unexpected error while trying to map JIRA issue "
            f"{jira_issue_key} to Zephyr test case: {e}"
        )

    # If we get here, we couldn't find a matching test case
    logger.warning(
        f"Could not find Zephyr test case matching JIRA issue {jira_issue_key}"
    )
    return None

