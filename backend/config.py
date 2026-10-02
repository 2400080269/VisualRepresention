"""
Configuration module for FastAPI backend.
Loads settings from .env file with secure defaults and path resolutions.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory: root of the project repository
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

# Load .env file from project root
env_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Student Performance Analytics & Early-Warning API")
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback_dev_secret_key_89ed61c073244866")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'data' / 'student_performance.db'}")

    # Paths
    ROOT_DIR: Path = PROJECT_ROOT
    DATA_DIR: Path = PROJECT_ROOT / "data"
    MODELS_DIR: Path = PROJECT_ROOT / "data" / "models"
    RAW_DATA_DIR: Path = PROJECT_ROOT / "data" / "raw"
    PROCESSED_DATA_DIR: Path = PROJECT_ROOT / "data" / "processed"
    SQLITE_DB_PATH: Path = PROJECT_ROOT / "data" / "student_performance.db"

    # CORS
    _raw_origins: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501")
    ALLOWED_ORIGINS: list[str] = [origin.strip() for origin in _raw_origins.split(",") if origin.strip()]

    # Uploads
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))

settings = Settings()
