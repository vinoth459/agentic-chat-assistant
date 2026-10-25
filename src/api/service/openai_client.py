"""OpenAI Responses API implementation."""  # Uses the OpenAI SDK to send model requests and keep conversation state in provider IDs.

from openai import OpenAI, OpenAIError  # Import the OpenAI client and its SDK-specific exception type.

from src.api.service.client_factory import ClientResponse, ProviderRequestError  # Shared response format and provider-specific failure wrapper.
from src.config.model_config import get_model_config  # Resolve the OpenAI model name from app config.
from src.config.settings import get_api_key  # Read the configured OpenAI API key.
from src.constants.app_constants import AppConstants  # Shared system instruction default for all provider calls.
from src.enums.error_codes import ErrorCode  # Error code used when the provider configuration is missing.
from src.enums.provider_enum import Provider  # Provider enum for the OpenAI route.
from src.exceptions.custom_exception import AppException  # Exception wrapper for configuration/readiness problems.


class OpenAIChatClient:
    def respond(
        self,
        prompt: str,
        previous_interaction_id: str | None = None,
        system_instruction: str = AppConstants.SAFETY_SYSTEM_INSTRUCTION,
    ) -> ClientResponse:
        try:
            api_key = get_api_key(Provider.OPENAI.value)  # Load the OpenAI API key from the environment.
        except AppException as error:
            raise ProviderRequestError(str(error), ErrorCode.PROVIDER_CONFIGURATION) from error  # Convert missing config into a provider request error.

        try:
            with OpenAI(api_key=api_key) as client:  # Create a client context that cleans up resources after the request.
                model_name = get_model_config(Provider.OPENAI).model_name  # Resolve the model name configured for OpenAI.
                if previous_interaction_id:
                    response = client.responses.create(
                        model=model_name,  # The configured OpenAI model to call.
                        input=prompt,  # Message content sent to the model.
                        previous_response_id=previous_interaction_id,  # Continue the same conversation with the prior response id.
                        instructions=system_instruction,  # Send the safety policy to the model before the prompt.
                    )
                else:
                    response = client.responses.create(
                        model=model_name,  # Initial model call without prior conversation state.
                        input=prompt,  # New user input for the provider.
                        instructions=system_instruction,  # Safety-first instruction injected before the user request.
                    )
        except OpenAIError as error:
            raise ProviderRequestError(
                f"OpenAI API request failed ({type(error).__name__}). "
                "Check the API key, model name, quota, and API access."
            ) from error  # Wrap SDK-specific exceptions in the app's provider error format.

        return ClientResponse(
            interaction_id=response.id,  # Save the response id to continue conversation state.
            text=response.output_text or "(OpenAI returned no text.)",  # Fall back if the API returns no visible text.
        )


