"""CLI entry point for the web application."""  # This module starts the FastAPI server using command-line arguments.

import argparse  # Parse host, port, and reload flags passed to the script.

import uvicorn  # Run the ASGI server that serves the FastAPI application.


def main() -> None:  # Entry point called when the script is executed directly.
    parser = argparse.ArgumentParser(description="Run the chatapi_app web application.")  # Create the CLI help text and argument parser.
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the server to.")  # Bind the app to localhost by default.
    parser.add_argument("--port", default=8000, type=int, help="Port to bind the server to.")  # Use port 8000 unless the user overrides it.
    parser.add_argument("--reload", action="store_true", help="Enable development auto-reload.")  # Toggle hot-reload during local development.
    args = parser.parse_args()  # Read the CLI arguments into a structured settings object.
    uvicorn.run(
        "src.api.controller.chat:app",  # Import path for the canonical FastAPI app instance to run.
        host=args.host,  # Use the host chosen by the CLI.
        port=args.port,  # Use the port chosen by the CLI.
        reload=args.reload,  # Enable auto reload only when requested.
    )


if __name__ == "__main__":  # Run the script only when it is executed directly, not when imported.
    main()  # Call the main function to start the web server.
