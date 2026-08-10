import os
from dotenv import load_dotenv

load_dotenv()
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
if not AZURE_OPENAI_API_KEY:
    raise RuntimeError(
        "AZURE_OPENAI_API_KEY is not configured."
    )

AZURE_OPENAI_BASE_URL = os.getenv("AZURE_OPENAI_BASE_URL")
if not AZURE_OPENAI_BASE_URL:
    raise RuntimeError(
        "AZURE_OPENAI_BASE_URL is not configured."
    )

AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL")
if not AZURE_OPENAI_MODEL:
    raise RuntimeError(
        "AZURE_OPENAI_MODEL is not configured."
    )
