"""FastAPI routes for provider-backed chat, saved history, and verification."""  # Main HTTP layer that validates messages, routes them to a provider, and saves conversation history.

import uuid  # Generate unique ids for each new conversation record.
from datetime import datetime, timezone  # Track UTC timestamps for saved messages and conversation updates.
from typing import Any  # Flexible typing for JSON-like dictionaries returned by the API.

from fastapi import APIRouter, FastAPI, HTTPException, Request  # FastAPI essentials for routing, request access, and HTTP errors.
from fastapi.responses import FileResponse, JSONResponse  # Return frontend HTML or machine-readable JSON responses.
from pydantic import BaseModel, Field  # Validate request bodies and enforce input length constraints.

from src.api.service.client_factory import ProviderRequestError, create_client  # Create and call the correct provider adapter.
from src.config.app_config import APP_CONFIG  # App metadata used in FastAPI initialization.
from src.config.env_config import ENV_CONFIG  # Runtime paths for the views directory and app config.
from src.config.logging_config import configure_logging  # Shared logger used for request and provider-level diagnostics.
from src.constants.app_constants import AppConstants  # Shared app limits and safety instruction text.
from src.enums.error_codes import ErrorCode  # Stable error-code mapping for app exceptions.
from src.enums.provider_enum import Provider  # Supported providers for chat conversations.
from src.exceptions.custom_exception import AppException  # Typed app exceptions returned by sanitization and history helpers.
from src.utils.input_sanitizer import sanitize_message, sanitize_verification_claim  # Normalize and validate untrusted messages.
from src.utils.conversation_store import STORE_LOCK, load_store, save_store  # Local JSON conversation persistence helpers.

VIEWS_DIR = ENV_CONFIG.views_dir  # Directory where the browser UI HTML files live.
logger = configure_logging()  # Initialize a shared logger for controller-level diagnostics.

app = FastAPI(
    title=APP_CONFIG.project_name,  # Display name used by OpenAPI docs and API metadata.
    version=APP_CONFIG.version,  # Application version shown in FastAPI docs.
    description=APP_CONFIG.description,  # High-level description of the project.
)
router = APIRouter(prefix="/api")  # Prefix all API endpoints under /api.
app.include_router(router)  # Attach the route definitions to the main FastAPI app instance.
ERROR_STATUS_CODES = {
    ErrorCode.INVALID_PROVIDER: 422,  # Reject unsupported provider values as invalid input.
    ErrorCode.EMPTY_INPUT: 422,  # User input is empty after sanitization.
    ErrorCode.INPUT_TOO_LONG: 422,  # Input exceeds the allowed size threshold.
    ErrorCode.INPUT_CONTROL_CHARACTERS: 422,  # Invalid control characters are rejected.
    ErrorCode.INPUT_PROFANITY: 422,  # Blocked-language terms are rejected.
    ErrorCode.INPUT_PROMPT_INJECTION: 422,  # Prompt-injection content is blocked.
    ErrorCode.PROVIDER_CONFIGURATION: 503,  # Provider setup is incomplete (missing API key).
    ErrorCode.PROVIDER_REQUEST_FAILED: 502,  # Upstream provider request failed or timed out.
    ErrorCode.CONVERSATION_NOT_FOUND: 404,  # Requested conversation record is missing.
    ErrorCode.HISTORY_INVALID: 500,  # Conversation JSON is malformed or wrong shape.
    ErrorCode.HISTORY_READ_FAILED: 500,  # Local history read or parse failed.
    ErrorCode.HISTORY_SAVE_FAILED: 500,  # Saving the updated conversation store failed.
}


class CreateConversationRequest(BaseModel):
    provider: Provider = Provider.GEMINI  # New conversations default to the Gemini provider.


class MessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=AppConstants.MAX_MESSAGE_LENGTH)  # Enforce message constraints before validation.


class VerifyRequest(BaseModel):
    claim: str = Field(min_length=1, max_length=AppConstants.MAX_VERIFY_LENGTH)  # Enforce claim constraints before verification.


@app.exception_handler(AppException)
async def handle_app_exception(request: Request, error: AppException) -> JSONResponse:
    status_code = ERROR_STATUS_CODES[error.code]  # Translate the typed app error into an HTTP status code.
    logger.warning(
        "Application request rejected: %s %s (%s)",
        request.method,
        request.url.path,
        error.code.value,
    )  # Log the request path and error code for debugging and auditing.
    return JSONResponse(
        status_code=status_code,
        content={"detail": error.message, "code": error.code.value},
    )  # Return a standard JSON payload describing the specific validation or provider failure.


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()  # Build a UTC timestamp for saved conversations and messages.


def get_store() -> dict[str, Any]:
    return load_store()  # Read the local history JSON store from disk.


def get_conversation(store: dict[str, Any], conversation_id: str) -> dict[str, Any]:
    conversation = store["conversations"].get(conversation_id)  # Look up the chosen conversation by its unique id.
    if conversation is None:
        raise AppException(ErrorCode.CONVERSATION_NOT_FOUND)  # Reject requests for unknown conversation ids.
    return conversation  # Return the matching conversation dictionary.


def provider_response(provider: str, prompt: str, previous_id: str | None) -> tuple[str, str]:
    try:
        result = create_client(provider).respond(prompt, previous_id)  # Route the request to the provider-specific adapter.
    except ProviderRequestError as error:
        logger.error("Provider request failed for %s with code %s", provider, error.code.value)  # Log which provider failed and the underlying code.
        raise error  # Re-raise the provider failure so the API can return a normalized error.
    return result.interaction_id, result.text  # Return the provider interaction id and generated text.


@app.get("/")
def index() -> FileResponse:
    return FileResponse(VIEWS_DIR / "index.html")  # Serve the browser UI for the chat app.


@router.get("/providers")
def list_providers() -> list[dict[str, str]]:
    provider_names = {
        Provider.OPENAI: "OpenAI",  # Friendly display label for OpenAI.
        Provider.GEMINI: "Gemini",  # Friendly display label for Gemini.
    }
    return [
        {"id": provider.value, "name": provider_names[provider]}  # Return provider ids and readable names for the front-end.
        for provider in Provider
    ]


@router.get("/conversations")
def list_conversations() -> list[dict[str, Any]]:
    with STORE_LOCK:
        conversations = list(get_store()["conversations"].values())  # Load all saved conversations under a thread-safe lock.
    conversations.sort(key=lambda item: item["updated_at"], reverse=True)  # Display the newest conversations first.
    return [
        {
            "id": item["id"],  # Conversation id used by the frontend to fetch details.
            "title": item["title"],  # Conversation title shown in the list.
            "provider": item["provider"],  # Provider currently assigned to the conversation.
            "updated_at": item["updated_at"],  # Last update timestamp in ISO format.
            "message_count": len(item["messages"]),  # Count of stored prompt/response entries.
        }
        for item in conversations
    ]


@router.post("/conversations")
def create_conversation(request: CreateConversationRequest) -> dict[str, Any]:
    now = utc_now()  # Build the timestamp for the new conversation entry.
    conversation = {
        "id": str(uuid.uuid4()),  # Create a unique conversation id.
        "title": "New conversation",  # Initial title before the first message arrives.
        "provider": request.provider.value,  # Store the selected provider on the conversation record.
        "created_at": now,  # Created timestamp.
        "updated_at": now,  # Updated timestamp.
        "latest_interaction_ids": {"openai": None, "gemini": None},  # Keep the latest provider interaction id for each provider.
        "messages": [],  # Start with an empty message list.
    }
    with STORE_LOCK:
        store = get_store()  # Load the local JSON conversation store.
        store["conversations"][conversation["id"]] = conversation  # Save the new conversation record to the store.
        save_store(store)  # Persist the updated store to disk.
    return conversation  # Return the saved conversation metadata to the frontend.


@router.get("/conversations/{conversation_id}")
def read_conversation(conversation_id: str) -> dict[str, Any]:
    with STORE_LOCK:
        store = get_store()  # Recover the latest conversation JSON store.
        return get_conversation(store, conversation_id)  # Return the full conversation record by id.


@router.post("/conversations/{conversation_id}/messages")
def send_message(conversation_id: str, request: MessageRequest) -> dict[str, Any]:
    message = sanitize_message(request.message)  # Validate and normalize the user message before sending it to the provider.

    with STORE_LOCK:
        store = get_store()  # Load the current JSON conversation store.
        conversation = get_conversation(store, conversation_id)  # Retrieve the relevant conversation record.
        provider = conversation["provider"]  # Identify which provider this conversation uses.
        previous_id = conversation["latest_interaction_ids"].get(provider)  # Read the last provider interaction id for this conversation.
        interaction_id, answer = provider_response(provider, message, previous_id)  # Ask the selected model to answer the user message.
        now = utc_now()  # Create a timestamp for the message entry.
        conversation["latest_interaction_ids"][provider] = interaction_id  # Update the provider state to continue context in later turns.
        conversation["updated_at"] = now  # Mark the conversation as updated after the new message.
        if not conversation["messages"]:
            conversation["title"] = message[:60] + ("..." if len(message) > 60 else "")  # Generate a title from the first user message.
        conversation["messages"].append(
            {"kind": "chat", "user": message, "response": answer, "created_at": now}  # Save the user prompt and model answer in history.
        )
        save_store(store)  # Persist the updated conversation state to disk.
    return {"conversation_id": conversation_id, "response": answer, "created_at": now}  # Return the response payload for the frontend.


@router.post("/conversations/{conversation_id}/verify")
def verify_history(conversation_id: str, request: VerifyRequest) -> dict[str, Any]:
    claim = sanitize_verification_claim(request.claim)  # Validate and normalize the verification claim before prompting the model.

    with STORE_LOCK:
        store = get_store()  # Load the latest conversation store before verification.
        conversation = get_conversation(store, conversation_id)  # Fetch the target conversation record.
        provider = conversation["provider"]  # Reuse the conversation's provider for context continuity.
        previous_id = conversation["latest_interaction_ids"].get(provider)  # Retrieve the last interaction id for this provider.
        if not previous_id:
            raise HTTPException(
                status_code=400,
                detail="Send at least one chat message before verifying conversation history.",
            )  # Verification requires at least one existing message for evidence.

        prompt = (
            "Check the following question or claim against our earlier conversation. "
            "Use only statements from that conversation as evidence. Quote or summarize "
            "relevant statements, distinguish explicit statements from inferences, and "
            "say clearly if there is not enough information to verify it.\n\n"
            f"Question or claim: {claim}"
        )  # Build the evidence-based verification prompt.
        interaction_id, answer = provider_response(provider, prompt, previous_id)  # Ask the model to verify the claim using prior conversation context.
        now = utc_now()  # Capture a timestamp for the verification result.
        conversation["latest_interaction_ids"][provider] = interaction_id  # Update the provider history pointer after the verification prompt.
        conversation["updated_at"] = now  # Mark the conversation as updated after verification.
        conversation["messages"].append(
            {"kind": "verify", "user": claim, "response": answer, "created_at": now}  # Store the verification prompt and answer in the history.
        )
        save_store(store)  # Write the mutated conversation history back to disk.
    return {"conversation_id": conversation_id, "response": answer, "created_at": now}  # Return the verification result to the frontend.


