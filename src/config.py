"""
Configuration management for JIRA Ticket Reader application.

This module handles loading and validating JIRA credentials from
environment variables. It ensures that credentials are never
hardcoded in the source code and are only loaded from local .env files.

SECURITY WARNING: Never commit .env files or hardcode credentials!
"""

import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseSettings, Field, ValidationError

from src.exceptions import JiraConfigurationError

# Configure logging for this module
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    This class uses Pydantic BaseSettings to validate and load
    configuration from environment variables. Credentials are
    loaded from a local .env file (never committed to Git).

    Attributes:
        jira_server_url: The base URL of the JIRA instance.
        jira_username: JIRA username or email address.
        jira_api_token: JIRA API token for authentication.

    Raises:
        JiraConfigurationError: If required environment variables
            are missing or invalid.
    """

    # JIRA server URL - must be provided
    jira_server_url: str = Field(
        ...,
        env="JIRA_SERVER_URL",
        description="Base URL of the JIRA instance (e.g., https://your-instance.atlassian.net)",
    )

    # JIRA username/email - must be provided
    jira_username: str = Field(
        ...,
        env="JIRA_USERNAME",
        description="JIRA username or email address",
    )

    # JIRA API token - must be provided
    # SECURITY: This is sensitive data - never log or expose this value!
    jira_api_token: str = Field(
        ...,
        env="JIRA_API_TOKEN",
        description="JIRA API token for authentication",
    )

    class Config:
        """
        Pydantic configuration for Settings.

        Configures environment variable loading from .env file.
        """

        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allow case-insensitive environment variable names
        case_sensitive = False


def load_settings() -> Settings:
    """
    Load and validate application settings from environment variables.

    This function loads environment variables from a .env file in the
    project root directory and validates them using Pydantic. It provides
    clear error messages if credentials are missing or invalid.

    Returns:
        Settings: Validated settings object containing JIRA credentials.

    Raises:
        JiraConfigurationError: If .env file is missing, or if required
            environment variables are not set or invalid.

    Example:
        >>> settings = load_settings()
        >>> print(settings.jira_server_url)
        https://your-instance.atlassian.net
    """
    # Load environment variables from .env file
    # The .env file should be in the project root and is NOT committed to Git
    env_path = Path(__file__).parent.parent / ".env"

    try:
        # Load .env file if it exists
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
            logger.info(f"Loaded environment variables from {env_path}")
        else:
            logger.warning(
                f".env file not found at {env_path}. "
                "Please create .env file with JIRA credentials."
            )
            # Still try to load from environment (might be set in system)
            load_dotenv()

        # Validate and create settings object
        # Pydantic will raise ValidationError if required fields are missing
        settings = Settings()

        # Validate that server URL is properly formatted
        if not settings.jira_server_url.startswith(("http://", "https://")):
            raise JiraConfigurationError(
                f"JIRA_SERVER_URL must start with http:// or https://. "
                f"Got: {settings.jira_server_url}"
            )

        # Log successful configuration (but never log the token!)
        logger.info(
            f"Successfully loaded JIRA configuration for server: "
            f"{settings.jira_server_url}"
        )
        logger.info(f"Username: {settings.jira_username}")
        logger.debug("API token loaded (not displayed for security)")

        return settings

    except ValidationError as e:
        # Pydantic validation error - missing or invalid fields
        error_messages = []
        for error in e.errors():
            field = error.get("loc", ["unknown"])[0]
            error_messages.append(f"  - {field}: {error.get('msg', 'invalid')}")

        raise JiraConfigurationError(
            "Failed to load JIRA configuration. "
            "Please ensure the following environment variables are set:\n"
            "  - JIRA_SERVER_URL (e.g., https://your-instance.atlassian.net)\n"
            "  - JIRA_USERNAME (your JIRA username or email)\n"
            "  - JIRA_API_TOKEN (your JIRA API token)\n\n"
            "Create a .env file in the project root with these variables.\n"
            "See .env.example for a template.\n\n"
            f"Validation errors:\n" + "\n".join(error_messages)
        ) from e

    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error loading settings: {e}", exc_info=True)
        raise JiraConfigurationError(
            f"Failed to load configuration: {e}"
        ) from e

