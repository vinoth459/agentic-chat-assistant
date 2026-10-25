"""Run a Gemini chat that saves and resumes conversation history.

Add GEMINI_API_KEY to .env, then run:
    python tests/manual/gemini_history_chat.py

Commands:
    /history          Show locally saved turns
    /verify <question> Check a claim against the earlier conversation
    /new              Start a fresh conversation and clear local history
    exit or quit      End the chat
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

load_dotenv()

HISTORY_FILE = Path(__file__).with_name("gemini_history.json")
MODEL = "gemini-3.8-flash"


def load_history() -> dict[str, Any]:
    if not HISTORY_FILE.exists():
        return {"latest_interaction_id": None, "turns": []}

    try:
        history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read chat history from {HISTORY_FILE}: {error}") from error

    if (
        not isinstance(history, dict)
        or not isinstance(history.get("turns"), list)
        or (
            history.get("latest_interaction_id") is not None
            and not isinstance(history.get("latest_interaction_id"), str)
        )
    ):
        raise RuntimeError(f"Chat history has an invalid format: {HISTORY_FILE}")

    return history


def save_history(history: dict[str, Any]) -> None:
    temporary_file = HISTORY_FILE.with_suffix(".tmp")
    try:
        temporary_file.write_text(
            json.dumps(history, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_file.replace(HISTORY_FILE)
    except OSError as error:
        raise RuntimeError(f"Could not save chat history to {HISTORY_FILE}: {error}") from error


def main() -> int:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY is not set. Add it to your .env file.", file=sys.stderr)
        return 1

    try:
        history = load_history()
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1

    print("Chat started. Type /history, /verify <question>, /new, or exit.")

    try:
        with genai.Client(api_key=api_key) as client:
            while True:
                user_input = input("You: ").strip()
                if user_input.lower() in {"exit", "quit"}:
                    break
                if not user_input:
                    continue

                if user_input == "/history":
                    if not history["turns"]:
                        print("No saved conversation history.")
                    else:
                        for index, turn in enumerate(history["turns"], start=1):
                            print(f"\n[{index}] You: {turn['user']}")
                            print(f"    Gemini: {turn['gemini']}")
                    continue

                if user_input == "/new":
                    history = {"latest_interaction_id": None, "turns": []}
                    try:
                        save_history(history)
                    except RuntimeError as error:
                        print(error, file=sys.stderr)
                        return 1
                    print("Started a new conversation; saved local history was cleared.")
                    continue

                is_verification = user_input.startswith("/verify ")
                if user_input == "/verify" or (
                    is_verification and not user_input.removeprefix("/verify ").strip()
                ):
                    print("Usage: /verify <question or claim to check>")
                    continue

                prompt = user_input
                if is_verification:
                    claim = user_input.removeprefix("/verify ").strip()
                    prompt = (
                        "Check the following question or claim against our earlier conversation. "
                        "Quote or summarize relevant prior statements, distinguish what was "
                        "explicitly said from what is only inferred, and say if the history "
                        f"does not provide enough evidence.\n\n{claim}"
                    )

                latest_interaction_id = history["latest_interaction_id"]
                if latest_interaction_id:
                    interaction = client.interactions.create(
                        model=MODEL,
                        input=prompt,
                        previous_interaction_id=latest_interaction_id,
                        stream=False,
                    )
                else:
                    interaction = client.interactions.create(
                        model=MODEL,
                        input=prompt,
                        stream=False,
                    )
                answer = interaction.output_text or "(Gemini returned no text.)"
                if not interaction.id:
                    raise RuntimeError("Gemini returned an interaction without an ID.")
                history["latest_interaction_id"] = interaction.id
                history["turns"].append(
                    {
                        "user": user_input,
                        "gemini": answer,
                    }
                )
                save_history(history)
                print(f"Gemini: {answer}")
    except APIError as error:
        print(
            f"Gemini API request failed (status: {error.code}). "
            "Check the API key, model name, and API access.",
            file=sys.stderr,
        )
        return 1
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
