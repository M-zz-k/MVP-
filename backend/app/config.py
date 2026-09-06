import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in backend directory, parent workspace directory, and current directory
_backend_dir = Path(__file__).resolve().parents[1]
_root_dir = Path(__file__).resolve().parents[2]

if (_backend_dir / ".env").exists():
    load_dotenv(dotenv_path=_backend_dir / ".env", override=True)
if (_root_dir / ".env").exists():
    load_dotenv(dotenv_path=_root_dir / ".env", override=True)
load_dotenv(override=False)

class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

def get_settings():
    return Settings()
