"""Validate and normalize untrusted user input before provider requests."""  # Blocks unsafe content before a chat message or verification claim reaches the model.

import re  # Use regex patterns to catch prompt-injection phrases and blocked words.
import unicodedata  # Normalize Unicode and inspect control characters before validation.

from src.config.settings import get_blocked_terms  # Read the configured blocked-term list from environment settings.
from src.constants.app_constants import AppConstants  # Message-length limits used by the sanitizer.
from src.enums.error_codes import ErrorCode  # Machine-readable error codes for each validation failure.
from src.exceptions.custom_exception import AppException  # Raise typed exceptions when content is rejected.

PROMPT_INJECTION_PATTERNS = (
    re.compile(r"\bignore\s+(?:all\s+)?(?:previous|prior|above|system)\s+instructions?\b", re.I),  # Detects attempts to override earlier system instructions.
    re.compile(r"\bignore\s+(?:the\s+)?(?:system|developer|safety|security)\s+(?:prompt|instructions?|rules?)\b", re.I),  # Searches for explicit instruction-suppression phrases.
    re.compile(r"\b(?:disregard|override|forget)\s+(?:all\s+)?(?:previous\s+|prior\s+|system\s+)?instructions?\b", re.I),  # Flags requests to forget or bypass instructions.
    re.compile(r"\b(?:reveal|print|show|output|repeat)\b.{0,80}\b(?:system prompt|developer instructions|api key|secrets?|credentials?)\b", re.I),  # Rejects accidental or malicious secret-disclosure tries.
    re.compile(r"\b(?:show|dump|print|output)\s+(?:all\s+)?(?:environment|env)\s+variables\b", re.I),  # Blocks environment-variable dumping requests.
    re.compile(r"\b(?:act as|pretend to be)\s+(?:the\s+)?(?:system|developer)\b", re.I),  # Refuses role-play attempts to impersonate trusted system roles.
)


def sanitize_user_input(value: str, *, max_length: int) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip()  # Normalize Unicode text and remove surrounding whitespace.
    if not normalized:
        raise AppException(ErrorCode.EMPTY_INPUT)  # Reject blank strings before calling the provider.
    if len(normalized) > max_length:
        raise AppException(ErrorCode.INPUT_TOO_LONG)  # Enforce the configured maximum input length.
    if any(unicodedata.category(char) == "Cc" and char not in "\n\t\r" for char in normalized):
        raise AppException(ErrorCode.INPUT_CONTROL_CHARACTERS)  # Reject control characters that can break formatting or parsing.

    canonical = " ".join(normalized.casefold().split())  # Lowercase and collapse repeated whitespace for consistent validation.
    for term in get_blocked_terms():
        term_pattern = r"\b" + r"\s+".join(re.escape(part) for part in term.casefold().split()) + r"\b"  # Build a safe regex for each blocked term.
        if re.search(term_pattern, canonical):
            raise AppException(ErrorCode.INPUT_PROFANITY)  # Reject profanity or customized blocked terms.

    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(canonical):
            raise AppException(ErrorCode.INPUT_PROMPT_INJECTION)  # Prevent prompt-injection phrases from reaching the model.

    return normalized  # Return the safe, normalized version of the user input.


def sanitize_message(value: str) -> str:
    return sanitize_user_input(value, max_length=AppConstants.MAX_MESSAGE_LENGTH)  # Validate chat text using the message length limit.


def sanitize_verification_claim(value: str) -> str:
    return sanitize_user_input(value, max_length=AppConstants.MAX_VERIFY_LENGTH)  # Validate verification claims using the shorter claim length limit.


