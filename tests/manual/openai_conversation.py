"""Run a simple multi-turn OpenAI conversation.

Add OPENAI_API_KEY to .env, then run:
    python tests/manual/openai_conversation.py
"""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

load_dotenv()


def main() -> int:
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set. Add it to your .env file.", file=sys.stderr)
        return 1

    previous_response_id = None
    print("Chat started. Type 'exit' or 'quit' to end.")

    try:
        with OpenAI() as client:
            while True:
                question = input("You: ").strip()
                if question.lower() in {"exit", "quit"}:
                    break
                if not question:
                    continue

                if previous_response_id:
                    response = client.responses.create(
                        model="gpt-5.6",
                        input=question,
                        previous_response_id=previous_response_id,
                    )
                else:
                    response = client.responses.create(
                        model="gpt-5.6",
                        input=question,
                    )
                previous_response_id = response.id
                print(f"Assistant: {response.output_text}")
    except OpenAIError as error:
        print(f"OpenAI API request failed: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
