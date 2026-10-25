# Manual API examples

These standalone scripts were moved out of the application root because the
FastAPI web app is now the main interface. Run commands from the project root:

```powershell
python tests/manual/test_openai_api.py
python tests/manual/test_gemini_api.py
python tests/manual/openai_conversation.py
python tests/manual/gemini_conversation.py
python tests/manual/gemini_history_chat.py
```

They read their API keys from the root `.env` file. Do not commit that file.
