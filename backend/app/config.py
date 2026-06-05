from pydantic_settings import BaseSettings
from functools import lru_cache
import os

# Resolve paths: works whether run from backend/ or project root
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/


def _find_policy_file() -> str:
    """Find policy_terms.json in multiple possible locations."""
    candidates = [
        os.path.join(_BACKEND_DIR, "policy_terms.json"),           # backend/policy_terms.json
        os.path.join(_BACKEND_DIR, "..", "policy_terms.json"),      # project_root/policy_terms.json
        os.path.join(os.getcwd(), "policy_terms.json"),             # cwd/policy_terms.json
    ]
    for path in candidates:
        if os.path.exists(path):
            return os.path.abspath(path)
    return candidates[0]  # Default to backend/ location


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./plum_opd.db"

    # OpenAI
    openai_api_key: str = ""

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Tesseract
    tesseract_path: str = "tesseract"

    # Uploads
    upload_dir: str = "./uploads"

    # App
    app_env: str = "development"
    app_name: str = "Plum OPD Adjudicator"
    app_version: str = "0.1.0"

    # Policy (loaded from file — auto-detected path)
    policy_terms_path: str = _find_policy_file()

    # Limits
    manual_review_threshold_amount: float = 25000.0
    manual_review_threshold_confidence: float = 0.70
    claim_submission_window_days: int = 30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
