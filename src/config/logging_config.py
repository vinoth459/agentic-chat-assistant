"""Console and rotating file logging configuration."""  # Creates a logger that writes both to the console and a rotating file.

import logging  # Standard library logging module for app diagnostics.
from logging.handlers import RotatingFileHandler  # Use a rotating file handler to keep logs manageable.

from src.config.env_config import ENV_CONFIG  # Pull the configured paths and log filename.


def configure_logging(name: str = "chatapi_app") -> logging.Logger:  # Create or reuse a named logger for the app.
    logger = logging.getLogger(name)  # Get the logger associated with the application name.
    logger.setLevel(logging.INFO)  # Record info-level events and above.
    logger.propagate = False  # Stop log records from being duplicated to the root logger.
    if logger.handlers:  # Reuse a logger that is already configured instead of creating duplicates.
        return logger

    ENV_CONFIG.log_dir.mkdir(parents=True, exist_ok=True)  # Ensure the log directory exists before writing logs.
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Standard timestamp and message format for each log entry.
        datefmt="%Y-%m-%d %H:%M:%S",  # Use a simple and readable timestamp format.
    )
    stream_handler = logging.StreamHandler()  # Send log messages to the terminal for local debugging.
    stream_handler.setFormatter(formatter)  # Apply the same formatter to terminal output.
    file_handler = RotatingFileHandler(
        ENV_CONFIG.log_dir / ENV_CONFIG.log_filename,  # Store log data in the configured log file.
        maxBytes=2_000_000,  # Rotate the log file after it exceeds 2 MB.
        backupCount=3,  # Keep up to three historical log files on disk.
        encoding="utf-8",  # Use UTF-8 to safely store text logs.
    )
    file_handler.setFormatter(formatter)  # Use the same formatting for file-based log entries.
    logger.addHandler(stream_handler)  # Attach the console log handler.
    logger.addHandler(file_handler)  # Attach the rotating file handler.
    return logger  # Return the configured logger so callers can log events.


