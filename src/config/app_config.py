"""Application metadata configuration."""  # Provides a single source of truth for FastAPI metadata and app identity.

from dataclasses import dataclass  # Use dataclass so configuration values are typed and easy to read.

from src.constants.app_constants import AppConstants  # Reuse shared app settings such as project name and version.


@dataclass(frozen=True)
class AppConfig:  # Container for information shown in the FastAPI docs and UI.
    project_name: str = AppConstants.PROJECT_NAME  # Name displayed in the generated API metadata.
    version: str = AppConstants.APP_VERSION  # App version exposed in FastAPI and docs.
    description: str = "Provider-based chat API with saved history and verification."  # High-level app summary.


APP_CONFIG = AppConfig()  # Create the singleton configuration object for the application.


