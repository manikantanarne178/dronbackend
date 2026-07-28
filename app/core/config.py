from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()


class Settings:

    PROJECT_NAME = "DroneVision API"

    VERSION = "1.0.0"

    DATABASE_URL = os.getenv("DATABASE_URL")

    SECRET_KEY = os.getenv("SECRET_KEY")

    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    BASE_DIR = Path(__file__).resolve().parent.parent

    UPLOAD_DIR = BASE_DIR / "uploads" / "images"

    OUTPUT_DIR = BASE_DIR / "outputs"

    PROJECTS_DIR = OUTPUT_DIR / "projects"

    REPORTS_DIR = OUTPUT_DIR / "reports"


settings = Settings()