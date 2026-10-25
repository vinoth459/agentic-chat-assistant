"""Compatibility import for `uvicorn app:app`."""  # Expose the main FastAPI app under the legacy uvicorn entrypoint name.

from src.api.controller.chat import app  # Import the packaged FastAPI app instance from the canonical app package.

__all__ = ["app"]  # Export the app symbol for legacy tooling and direct imports.
