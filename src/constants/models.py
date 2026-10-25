"""Default model names for each supported chat provider."""  # Exposes the model mapping as a plain dictionary for runtime lookups.

from src.constants.app_constants import AppConstants  # Pull the default model definitions from the shared constants module.

MODELS = dict(AppConstants.PROVIDER_MODELS)  # Copy the provider/model mapping into a plain dictionary.


