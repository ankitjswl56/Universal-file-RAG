import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    qdrant_host: str
    qdrant_port: int
    sqlite_path: Path


def load_settings() -> Settings:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    sqlite_path = Path(os.environ.get("SQLITE_PATH", "./data/ufrag.db"))
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return Settings(
        gemini_api_key=api_key,
        qdrant_host=os.environ.get("QDRANT_HOST", "localhost"),
        qdrant_port=int(os.environ.get("QDRANT_PORT", "6333")),
        sqlite_path=sqlite_path,
    )
