"""Check GEMINI_API_KEY by making a small Gemini API request.

Add your key to .env as GEMINI_API_KEY=your-api-key, then run:
    python tests/manual/test_gemini_api.py
"""

import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

load_dotenv()


def main() -> int:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY is not set.", file=sys.stderr)
        return 1

    try:
        with genai.Client(api_key=api_key) as client:
            interaction = client.interactions.create(
                model="gemini-3.8-flash",
                input="Explain how AI works in a few words",
            )
    except APIError as error:
        print(
            f"Gemini API request failed (status: {error.code}). "
            "Check the API key, model name, and API access.",
            file=sys.stderr,
        )
        return 1

    print("API key is valid; successfully reached the Gemini API.")
    print(interaction.output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
