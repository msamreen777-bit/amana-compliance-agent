import os
from dotenv import load_dotenv

# Load variables from the .env file into the environment
load_dotenv()

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "gpt-4o")
    FAST_LLM_MODEL: str = os.getenv("FAST_LLM_MODEL", "gpt-4o-mini")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./.chroma")

settings = Settings()

if not settings.OPENAI_API_KEY:
    print("[WARNING] OPENAI_API_KEY not set. Ensure it is defined in your .env file.")
