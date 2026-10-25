"""Application exceptions with stable API error codes."""  # Wraps domain errors so callers can use consistent error codes and messages.

from src.enums.error_codes import ErrorCode  # Reuse the application-wide stable error code enum.


class AppException(Exception):
    def __init__(self, code: ErrorCode, message: str | None = None) -> None:
        self.code = code  # Save the machine-readable error identifier.
        self.message = message or code.message  # Use the enum's default detail message unless overridden.
        super().__init__(self.message)  # Raise the base exception with the final human-readable message.


