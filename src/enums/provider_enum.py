"""Supported model-provider identifiers."""  # Lists the providers accepted by the app and its route validation.

from enum import Enum  # Standard Python enum used for typed provider values.


class Provider(str, Enum):
    OPENAI = "openai"  # OpenAI chat provider identifier.
    GEMINI = "gemini"  # Gemini chat provider identifier.


