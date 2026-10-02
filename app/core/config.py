from dotenv import load_dotenv
import os
from pathlib import Path
from typing import Optional

# Load .env file for local development without overriding environment variables set in system / Render
load_dotenv(override=False)


def normalize_database_url(url: Optional[str]) -> str:
    """
    Safely normalizes database URLs for SQLAlchemy and psycopg (psycopg 3).
    Converts 'postgres://' and 'postgresql://' prefixes to 'postgresql+psycopg://'.
    Preserves query parameters (such as sslmode), usernames, passwords, and port configurations.
    Raises ValueError if DATABASE_URL is not set or empty.
    """
    if not url or not str(url).strip():
        raise ValueError("DATABASE_URL environment variable is not configured.")

    url = str(url).strip()

    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    elif url.startswith("postgresql+psycopg://"):
        pass  # Already in SQLAlchemy + psycopg3 format
    elif url.startswith("sqlite://"):
        pass  # SQLite format for local testing / development

    return url


class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "DroneVision API")
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY")

    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads" / "images"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    PROJECTS_DIR: Path = OUTPUT_DIR / "projects"
    REPORTS_DIR: Path = OUTPUT_DIR / "reports"

    @property
    def DATABASE_URL(self) -> str:
        raw_url = os.getenv("DATABASE_URL")
        return normalize_database_url(raw_url)


settings = Settings()