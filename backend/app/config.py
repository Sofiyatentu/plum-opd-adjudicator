from pydantic_settings import BaseSettings
from functools import lru_cache
import os


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

    # Policy (loaded from file, default path)
    policy_terms_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "policy_terms.json")

    # Limits
    manual_review_threshold_amount: float = 25000.0
    manual_review_threshold_confidence: float = 0.70
    claim_submission_window_days: int = 30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
