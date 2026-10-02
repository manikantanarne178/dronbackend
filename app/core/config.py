from dotenv import load_dotenv
import os
from pathlib import Path
from typing import Optional

# Load .env file for local development without overriding environment variables set in system / Render
load_dotenv(override=False)


def normalize_database_url(url: Optional[str]) -> str:
    """
    Safely normalizes database URLs for SQLAlchemy and psycopg/psycopg2.
    Converts 'postgres://' and 'postgresql://' prefixes to standard SQLAlchemy driver format.
    Preserves query parameters (such as sslmode), usernames, passwords, and port configurations.
    Raises ValueError if DATABASE_URL is not set or empty.
    """
    if not url or not str(url).strip():
        raise ValueError("DATABASE_URL environment variable is not configured.")

    url = str(url).strip()

    has_psycopg3 = False
    try:
        import psycopg
        has_psycopg3 = True
    except ImportError:
        pass

    driver_prefix = "postgresql+psycopg://" if has_psycopg3 else "postgresql+psycopg2://"

    if url.startswith("postgres://"):
        url = driver_prefix + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = driver_prefix + url[len("postgresql://"):]
    elif url.startswith("postgresql+psycopg://") and not has_psycopg3:
        url = "postgresql+psycopg2://" + url[len("postgresql+psycopg://"):]
    elif url.startswith("sqlite://"):
        pass

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
