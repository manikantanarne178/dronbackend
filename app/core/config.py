from dotenv import load_dotenv
import os

load_dotenv()

class Settings:

    PROJECT_NAME = "DroneVision API"

    VERSION = "1.0.0"

    DATABASE_URL = os.getenv("DATABASE_URL")

    SECRET_KEY = os.getenv("SECRET_KEY")

settings = Settings()