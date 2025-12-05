"""
Configuration management for JIRA Ticket Reader application.

This module handles loading and validating JIRA credentials from
environment variables. It ensures that credentials are never
hardcoded in the source code and are only loaded from local .env files.

SECURITY WARNING: Never commit .env files or hardcode credentials!
"""

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

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

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields that aren't defined in Settings
        # Don't set env_file here - we'll handle it in load_settings()
    )


def load_settings() -> Settings:
    """
    Load and validate application settings from environment variables.

    This function loads environment variables from a .env file in the project root.
    It validates them using Pydantic and provides clear error messages if
    credentials are missing or invalid.

    Returns:
        Settings: Validated settings object containing JIRA credentials.

    Raises:
        JiraConfigurationError: If credential file is missing, or if required
            environment variables are not set or invalid.

    Example:
        >>> settings = load_settings()
        >>> print(settings.jira_server_url)
        https://your-instance.atlassian.net
    """
    # .env file in project root
    # SECURITY: This file contains sensitive credentials and is NOT committed to Git
    env_path = Path(__file__).parent.parent / ".env"

    try:
        # Load environment variables from .env file if it exists
        if env_path.exists():
            result = load_dotenv(dotenv_path=env_path, override=True)
            if result:
                logger.info(f"Loaded environment variables from: {env_path}")
                # Verify that at least one variable was loaded
                if not (
                    os.getenv("JIRA_SERVER_URL")
                    or os.getenv("JIRA_USERNAME")
                    or os.getenv("JIRA_API_TOKEN")
                ):
                    logger.warning(
                        f"File {env_path} exists but no JIRA environment "
                        "variables were found. Please check the file format. "
                        "Expected format: KEY=VALUE (one per line)"
                    )
            else:
                logger.warning(
                    f"Failed to load environment variables from {env_path}. "
                    "File may be empty or have incorrect format."
                )
        else:
            logger.warning(
                f".env file not found at {env_path}. "
                "Attempting to load from system environment variables."
            )
            # Try to load from system environment
            load_dotenv()

        # Validate and create settings object
        # Settings will read from os.environ which was populated by load_dotenv()
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
        missing_fields = []
        for error in e.errors():
            field = error.get("loc", ["unknown"])[0]
            msg = error.get("msg", "invalid")
            error_messages.append(f"  - {field}: {msg}")
            if "required" in msg.lower() or "field required" in msg.lower():
                missing_fields.append(field.upper())

        # Check which variables are actually missing from environment
        missing_vars = []
        if not os.getenv("JIRA_SERVER_URL"):
            missing_vars.append("JIRA_SERVER_URL")
        if not os.getenv("JIRA_USERNAME"):
            missing_vars.append("JIRA_USERNAME")
        if not os.getenv("JIRA_API_TOKEN"):
            missing_vars.append("JIRA_API_TOKEN")

        error_msg = (
            "Failed to load JIRA configuration. "
            "Please ensure the following environment variables are set:\n"
            "  - JIRA_SERVER_URL (e.g., https://your-instance.atlassian.net)\n"
            "  - JIRA_USERNAME (your JIRA username or email)\n"
            "  - JIRA_API_TOKEN (your JIRA API token)\n\n"
        )

        # Provide specific guidance based on what was found
        if env_path.exists() and missing_vars:
            error_msg += (
                f"The .env file at {env_path} was found, "
                "but it does not contain the required JIRA variables.\n"
                "Please add the following variables to that file:\n"
            )
            for var in missing_vars:
                error_msg += f"  {var}=your-value-here\n"
            error_msg += "\n"

        error_msg += (
            "Alternatively, create a .env file in the project root with these variables.\n"
            "See .env.example for a template.\n\n"
            f"Validation errors:\n" + "\n".join(error_messages)
        )

        raise JiraConfigurationError(error_msg) from e

    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error loading settings: {e}", exc_info=True)
        raise JiraConfigurationError(
            f"Failed to load configuration: {e}"
        ) from e
