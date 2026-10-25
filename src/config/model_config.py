"""Provider model configuration."""  # Maps each supported provider to the specific model name the app should use.

from dataclasses import dataclass  # Create a simple configuration object for model metadata.

from src.constants.models import MODELS  # Pull the list of default provider model names.
from src.enums.provider_enum import Provider  # Use the enum to constrain valid provider choices.


@dataclass(frozen=True)
class ModelConfig:  # Stores the provider and model chosen for an outbound request.
    provider: Provider  # The provider enum value for this configuration.
    model_name: str  # Model identifier to send to the provider API.


def get_model_config(provider: Provider) -> ModelConfig:  # Resolve a provider enum into a model configuration object.
    return ModelConfig(provider=provider, model_name=MODELS[provider.value])  # Build the config from the provider enum and model map.


