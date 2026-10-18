import os
from dotenv import load_dotenv

load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_BASE_URL = os.getenv("AZURE_OPENAI_BASE_URL")
AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL")

MS365_MCP_URL = os.getenv("MS365_MCP_URL")
MS365_CALLBACK_URL = os.getenv(
    "MS365_CALLBACK_URL",
    "http://localhost:8080/callback"
)


def require_config(**settings):
    missing = [name for name, value in settings.items() if not value]

    if missing:
        raise RuntimeError(
            f"Missing required configuration: {', '.join(missing)}"
        )