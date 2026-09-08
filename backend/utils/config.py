import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directories
BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent

# Load environment variables
if (BACKEND_DIR / ".env").exists():
    load_dotenv(dotenv_path=BACKEND_DIR / ".env", override=True)
if (ROOT_DIR / ".env").exists():
    load_dotenv(dotenv_path=ROOT_DIR / ".env", override=True)
load_dotenv(override=False)

MAPS_DIR = ROOT_DIR / "maps"
MAPS_DIR.mkdir(exist_ok=True)

GRAPHS_DIR = ROOT_DIR / "graphs"
GRAPHS_DIR.mkdir(exist_ok=True)


class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")


def get_settings() -> Settings:
    return Settings()
