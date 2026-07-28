from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.base import Base

# Import all models so SQLAlchemy registers them
from app.models.user import User
from app.models.project import Project

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,      # Enable SQL logs only in debug mode
    future=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)