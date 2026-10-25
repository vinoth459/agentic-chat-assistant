"""Check that OPENAI_API_KEY can authenticate with the OpenAI API.

PowerShell:
    Add your key to .env as OPENAI_API_KEY=your-api-key
    python tests/manual/test_openai_api.py
"""

import os
import sys

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

load_dotenv()


def main() -> int:
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set.", file=sys.stderr)
        return 1

    try:
        models = OpenAI().models.list()
    except AuthenticationError:
        print("Authentication failed. Check that OPENAI_API_KEY is valid.", file=sys.stderr)
        return 1
    except RateLimitError as error:
        print(f"API rate limit or quota error: {error}", file=sys.stderr)
        return 1
    except APIConnectionError as error:
        print(f"Could not connect to the OpenAI API: {error}", file=sys.stderr)
        return 1
    except APIStatusError as error:
        print(f"OpenAI API returned HTTP {error.status_code}: {error}", file=sys.stderr)
        return 1
    except OpenAIError as error:
        print(f"OpenAI API error: {error}", file=sys.stderr)
        return 1

    model_names = [model.id for model in models.data[:5]]
    print("API key is valid; successfully reached the OpenAI API.")
    if model_names:
        print("A few available models: " + ", ".join(model_names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
