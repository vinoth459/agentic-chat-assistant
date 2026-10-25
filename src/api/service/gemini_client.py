"""Gemini Interactions API implementation."""  # Calls the Gemini SDK so the app can send user prompts and continue provider-based conversations.

from google import genai  # Google GenAI SDK entrypoint for Gemini requests.
from google.genai import interactions as genai_interactions  # Typed Gemini interaction models used in the response validation.
from google.genai.errors import APIError  # Catch provider-specific errors thrown by the Google SDK.

from src.api.service.client_factory import ClientResponse, ProviderRequestError  # Shared client contract and error wrapper.
from src.config.model_config import get_model_config  # Resolve the configured Gemini model name.
from src.config.settings import get_api_key  # Read the Gemini API key from the runtime environment.
from src.constants.app_constants import AppConstants  # Shared safety instruction for gemini requests.
from src.enums.error_codes import ErrorCode  # Error code for provider misconfiguration.
from src.enums.provider_enum import Provider  # Gemini provider enum value.
from src.exceptions.custom_exception import AppException  # Base app exception used for missing configuration.


class GeminiAIClient:
    def respond(
        self,
        prompt: str,
        previous_interaction_id: str | None = None,
        system_instruction: str = AppConstants.SAFETY_SYSTEM_INSTRUCTION,
    ) -> ClientResponse:
        try:
            api_key = get_api_key(Provider.GEMINI.value)  # Load the configured Gemini API key from the environment.
        except AppException as error:
            raise ProviderRequestError(str(error), ErrorCode.PROVIDER_CONFIGURATION) from error  # Wrap missing configuration into a provider request error.

        try:
            with genai.Client(api_key=api_key) as client:  # Open a Gemini API client with automatic cleanup.
                model_name = get_model_config(Provider.GEMINI).model_name  # Resolve the configured Gemini model name.
                if previous_interaction_id:
                    interaction = client.interactions.create(
                        model=model_name,  # Continue the conversation using the configured Gemini model.
                        input=prompt,  # Send the user's latest message to Gemini.
                        previous_interaction_id=previous_interaction_id,  # Maintain provider context across the conversation.
                        system_instruction=system_instruction,  # Safety guidance sent before the user message.
                        stream=False,  # Request a standard non-streaming response.
                    )
                else:
                    interaction = client.interactions.create(
                        model=model_name,  # Start a fresh Gemini interaction for the user message.
                        input=prompt,  # User content sent to the provider.
                        system_instruction=system_instruction,  # Guidance that keeps the provider safe and predictable.
                        stream=False,  # Force a standard response object rather than stream events.
                    )
        except APIError as error:
            raise ProviderRequestError(
                f"Gemini API request failed with status {error.code}. "
                "Check the API key, model name, and API access."
            ) from error  # Standardize the upstream Google API failure into a typed app error.

        if not isinstance(interaction, genai_interactions.Interaction):
            raise ProviderRequestError("Gemini returned a streaming response when a standard response was expected.")  # Reject unexpected streaming objects.
        if not interaction.id:
            raise ProviderRequestError("Gemini returned an interaction without an ID.")  # Require a valid provider id before storing conversation context.

        return ClientResponse(
            interaction_id=interaction.id,  # Save the Gemini interaction id for follow-up history continuity.
            text=interaction.output_text or "(Gemini returned no text.)",  # Use a fallback if the model failed to produce visible output.
        )


