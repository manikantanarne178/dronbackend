from dotenv import load_dotenv
import os
from pathlib import Path
from typing import Optional

# Load .env file for local development without overriding environment variables set in system / Render
load_dotenv(override=False)


def normalize_database_url(url: Optional[str], default_sqlite_path: Path) -> str:
    """
    Safely normalizes database URLs for SQLAlchemy and psycopg/psycopg2.
    Falls back to SQLite if DATABASE_URL is not configured or points to unreachable localhost on Render/Cloud.
    """
    if not url or not str(url).strip():
        return f"sqlite:///{default_sqlite_path}"

    url = str(url).strip()

    # Guard against localhost/127.0.0.1 when running on cloud hosts (e.g. Render) where no local postgres exists
    is_cloud_env = bool(os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID") or os.getenv("PORT"))
    is_localhost = any(h in url.lower() for h in ["localhost", "127.0.0.1"])
    if is_cloud_env and is_localhost:
        return f"sqlite:///{default_sqlite_path}"

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
    SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY", "dronevision_secret_key_prod_2026")

    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads" / "images"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    PROJECTS_DIR: Path = OUTPUT_DIR / "projects"
    REPORTS_DIR: Path = OUTPUT_DIR / "reports"

    @property
    def DATABASE_URL(self) -> str:
        raw_url = os.getenv("DATABASE_URL")
        sqlite_fallback = self.BASE_DIR / "dronevision.db"
        return normalize_database_url(raw_url, sqlite_fallback)


settings = Settings()
