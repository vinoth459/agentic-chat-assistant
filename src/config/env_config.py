"""Runtime filesystem paths for the application."""  # Provides consistent paths for logs, UI templates, and saved chat history.

from dataclasses import dataclass  # Use a data class to store path-related configuration.
from pathlib import Path  # Handle filesystem paths in a cross-platform way.

from src.constants.app_constants import AppConstants  # Use shared application file names and settings.


@dataclass(frozen=True)
class EnvConfig:  # Stores the paths the app needs at runtime.
    project_root: Path  # Root directory of the current project.
    views_dir: Path  # Folder containing the frontend HTML files.
    log_dir: Path  # Directory for rotating application logs.
    conversation_file: Path  # File used to persist chat history.
    log_filename: str = AppConstants.APP_LOG_FILENAME  # Name of the generated log file.


def get_env_config() -> EnvConfig:  # Build the environment configuration for this installation.
    project_root = Path(__file__).resolve().parents[2]  # Move from src/config to the project root.
    return EnvConfig(
        project_root=project_root,  # Save the resolved project root path.
        views_dir=project_root / "views",  # Point to the front-end template directory.
        log_dir=project_root / "logs",  # Point to the logs directory used for app diagnostics.
        conversation_file=project_root / "data" / AppConstants.CONVERSATION_FILENAME,  # Save persisted conversations in a dedicated runtime-data folder.
    )


ENV_CONFIG = get_env_config()  # Create the singleton runtime environment object.


