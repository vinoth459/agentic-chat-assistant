"""Run a simple multi-turn Gemini conversation.

Add GEMINI_API_KEY to .env, then run:
    python tests/manual/gemini_conversation.py
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
        print("GEMINI_API_KEY is not set. Add it to your .env file.", file=sys.stderr)
        return 1

    previous_interaction_id = None
    print("Chat started. Type 'exit' or 'quit' to end.")

    try:
        with genai.Client(api_key=api_key) as client:
            while True:
                question = input("You: ").strip()
                if question.lower() in {"exit", "quit"}:
                    break
                if not question:
                    continue

                if previous_interaction_id:
                    interaction = client.interactions.create(
                        model="gemini-3.8-flash",
                        input=question,
                        previous_interaction_id=previous_interaction_id,
                    )
                else:
                    interaction = client.interactions.create(
                        model="gemini-3.8-flash",
                        input=question,
                    )
                previous_interaction_id = interaction.id
                print(f"Gemini: {interaction.output_text}")
    except APIError as error:
        print(
            f"Gemini API request failed (status: {error.code}). "
            "Check the API key, model name, and API access.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
