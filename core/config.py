import os
from dotenv import load_dotenv
load_dotenv()

MODEL = os.getenv("LLM_MODEL", "gemma-4-26b-a4b-it")
PROVIDER = os.getenv("LLM_PROVIDER", "google_genai")
MAX_INPUT_CHARS = 30_000
THINKING_LEVEL = os.getenv("LLM_THINKING_LEVEL", "minimal")