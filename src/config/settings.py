"""Environment-backed application settings."""  # Reads runtime config from environment variables and project defaults.

import os  # Access environment variables such as API keys and custom blocked terms.

from dotenv import load_dotenv  # Load values from the project's .env file automatically.

from src.constants.app_constants import AppConstants  # Shared defaults for blocked words and app metadata.
from src.enums.error_codes import ErrorCode  # Error codes for provider and configuration failures.
from src.enums.provider_enum import Provider  # Supported provider enum values.
from src.exceptions.custom_exception import AppException  # Typed exception for invalid or missing config.

load_dotenv()  # Load environment variables from the local .env file before use.

API_KEY_ENV_VARS = {
    Provider.OPENAI.value: "OPENAI_API_KEY",  # Environment variable name for the OpenAI API key.
    Provider.GEMINI.value: "GEMINI_API_KEY",  # Environment variable name for the Gemini API key.
}


def get_api_key(provider: str) -> str:  # Return the configured key for the selected provider.
    try:
        env_var = API_KEY_ENV_VARS[provider]  # Look up the matching environment variable for the provider.
    except KeyError as error:
        raise AppException(ErrorCode.INVALID_PROVIDER) from error  # Reject unsupported providers early.
    api_key = os.getenv(env_var)  # Read the actual API key value from the environment.
    if not api_key:
        raise AppException(
            ErrorCode.PROVIDER_CONFIGURATION,
            f"{env_var} is not set. Add it to the project's .env file.",
        )  # Raise a helpful configuration error when the key is missing.
    return api_key  # Return the validated API key for outbound calls.


def get_blocked_terms() -> tuple[str, ...]:  # Return user-blocked words or the default profanity list.
    configured_terms = os.getenv("CHAT_BLOCKED_TERMS")  # Optional comma-separated override from environment or .env.
    if configured_terms is None:
        return AppConstants.DEFAULT_BLOCKED_TERMS  # Use the built-in list if no override is supplied.
    return tuple(term.strip() for term in configured_terms.split(",") if term.strip())  # Normalize the custom list to clean strings.


