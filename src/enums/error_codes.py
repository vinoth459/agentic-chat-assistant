"""Stable application error codes for API responses and logs."""  # Centralizes the machine-readable status codes used throughout the app.

from enum import Enum  # Standard enum support for strongly typed application errors.


class ErrorCode(str, Enum):
    INVALID_PROVIDER = "CHAT_001"  # A provider that is not supported by the app was requested.
    EMPTY_INPUT = "INPUT_001"  # The message or verification claim was empty after normalization.
    INPUT_TOO_LONG = "INPUT_002"  # The message exceeds the configured length limit.
    INPUT_CONTROL_CHARACTERS = "INPUT_003"  # Input contains disallowed control characters.
    INPUT_PROFANITY = "INPUT_004"  # The message contains a blocked word or abusive term.
    INPUT_PROMPT_INJECTION = "INPUT_005"  # The input appears to attempt an instruction override or secret leak.
    PROVIDER_CONFIGURATION = "PROVIDER_001"  # The provider is missing an API key or setup configuration.
    PROVIDER_REQUEST_FAILED = "PROVIDER_002"  # The upstream provider returned an error or timed out.
    CONVERSATION_NOT_FOUND = "HISTORY_001"  # The selected conversation id does not exist in storage.
    HISTORY_INVALID = "HISTORY_002"  # The saved history file layout or data shape is invalid.
    HISTORY_READ_FAILED = "HISTORY_003"  # Reading the local conversation store failed.
    HISTORY_SAVE_FAILED = "HISTORY_004"  # Writing updates back to the local conversation store failed.

    @property
    def message(self) -> str:
        messages = {
            self.INVALID_PROVIDER: "The selected provider is not supported.",  # Standard error shown when a provider is invalid.
            self.EMPTY_INPUT: "Input cannot be empty.",  # Friendly confirmation that a blank value was rejected.
            self.INPUT_TOO_LONG: "Input exceeds the allowed length.",  # Length-limit validation message.
            self.INPUT_CONTROL_CHARACTERS: "Input contains unsupported control characters.",  # Rejects non-printable or unsafe control bytes.
            self.INPUT_PROFANITY: "Please rewrite the message without blocked terms.",  # Guidance to retry with cleaner wording.
            self.INPUT_PROMPT_INJECTION: "Input contains an instruction override that is not allowed.",  # Prompts the user to remove injection-like content.
            self.PROVIDER_CONFIGURATION: "The selected provider is not configured.",  # Missing key message for runtime setup errors.
            self.PROVIDER_REQUEST_FAILED: "The model provider request failed.",  # Generic provider failure wording.
            self.CONVERSATION_NOT_FOUND: "Conversation not found.",  # Standard 404-like message for missing conversations.
            self.HISTORY_INVALID: "Conversation history has an invalid format.",  # Raised when stored JSON is malformed.
            self.HISTORY_READ_FAILED: "Conversation history could not be read.",  # Indicates a disk or parsing failure.
            self.HISTORY_SAVE_FAILED: "Conversation history could not be saved.",  # Indicates a persistent write failure.
        }
        return messages[self]  # Return the human-readable validation or storage message.


