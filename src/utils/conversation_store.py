"""Local JSON persistence for conversations."""  # Saves the chat history to a local JSON file with safe read/write semantics.

import json  # Serialize and deserialize the conversation store to JSON.
import threading  # Prevent simultaneous writes to the JSON conversation file.
from typing import Any  # Use flexible values when reading and writing dictionary-based store objects.

from src.config.env_config import ENV_CONFIG  # Read the configured conversation-file path.
from src.enums.error_codes import ErrorCode  # Error enums used when the history store is invalid or unreadable.
from src.exceptions.custom_exception import AppException  # Raise typed exceptions for history failures.

STORE_FILE = ENV_CONFIG.conversation_file  # Global path to the conversation-store file.
STORE_LOCK = threading.Lock()  # Shared lock to serialize access to all conversation operations.


def load_store() -> dict[str, Any]:
    STORE_FILE.parent.mkdir(parents=True, exist_ok=True)  # Ensure the runtime-data directory exists before reading or creating the store.
    if not STORE_FILE.exists():  # Create an empty JSON store when no conversation history file exists yet.
        return {"conversations": {}}

    try:
        store = json.loads(STORE_FILE.read_text(encoding="utf-8"))  # Parse the saved JSON conversation data.
    except (OSError, json.JSONDecodeError) as error:
        raise AppException(ErrorCode.HISTORY_READ_FAILED) from error  # Surface unreadable or malformed history as a typed error.

    if not isinstance(store, dict) or not isinstance(store.get("conversations"), dict):
        raise AppException(ErrorCode.HISTORY_INVALID)  # Reject invalid conversation-store schemas.

    for conversation in store["conversations"].values():
        if not isinstance(conversation, dict):
            raise AppException(ErrorCode.HISTORY_INVALID)  # Each conversation entry must be a dictionary.
        provider = conversation.setdefault("provider", "gemini")  # Preserve compatibility with older Gemini-based histories.
        ids = conversation.setdefault("latest_interaction_ids", {})  # Ensure the modern interaction-state map exists.
        if not isinstance(ids, dict):
            raise AppException(ErrorCode.HISTORY_INVALID)  # Reject non-dictionary interaction metadata.
        legacy_id = conversation.pop("latest_interaction_id", None)  # Remove the legacy key after migrating values.
        if legacy_id and provider == "gemini":
            ids.setdefault("gemini", legacy_id)  # Preserve any old Gemini interaction id when present.
        ids.setdefault("openai", None)  # Keep an empty OpenAI slot for provider parity.
        ids.setdefault("gemini", None)  # Keep an empty Gemini slot for provider parity.

    return store  # Return the normalized conversation store object.


def save_store(store: dict[str, Any]) -> None:
    STORE_FILE.parent.mkdir(parents=True, exist_ok=True)  # Ensure the runtime-data folder exists before saving conversation updates.
    temporary_file = STORE_FILE.with_suffix(".tmp")  # Write to a temp file and swap it in to avoid partial writes.
    try:
        temporary_file.write_text(
            json.dumps(store, ensure_ascii=False, indent=2) + "\n",  # Save human-readable JSON with UTF-8 text formatting.
            encoding="utf-8",
        )
        temporary_file.replace(STORE_FILE)  # Replace the live store atomically only after the write succeeds.
    except OSError as error:
        raise AppException(ErrorCode.HISTORY_SAVE_FAILED) from error  # Raise a typed error if the conversation store cannot be saved.


