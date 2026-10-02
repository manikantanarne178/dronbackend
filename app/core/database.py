from typing import Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.base import Base

# Import all models so SQLAlchemy registers them
from app.models.user import User
from app.models.project import Project
from app.models.rule_config import RuleConfig
from app.models.autodcr_models import (
    AutoDCRProject,
    AutoDCRDrawing,
    AutoDCRAnalysis,
    RuleValidationResult,
    ComplianceReportModel,
    AuditLog,
)


def get_engine_args(db_url: str) -> Dict[str, Any]:
    """
    Builds production-safe engine arguments and connection pool settings
    tailored to the database driver and environment.
    """
    engine_args: Dict[str, Any] = {
        "echo": settings.DEBUG,
        "future": True,
    }

    if db_url.startswith("sqlite"):
        engine_args["connect_args"] = {"check_same_thread": False}
    elif db_url.startswith("postgresql"):
        # Production connection pool settings
        engine_args["pool_pre_ping"] = True
        engine_args["pool_recycle"] = 300
        engine_args["pool_size"] = 10
        engine_args["max_overflow"] = 20

        # Enable SSL for remote cloud databases (e.g. Render) when not explicitly set in the URL
        is_local = any(h in db_url for h in ["localhost", "127.0.0.1"])
        if not is_local and "sslmode=" not in db_url:
            engine_args["connect_args"] = {"sslmode": "prefer"}

    return engine_args


# Initialize SQLAlchemy Engine
engine = create_engine(
    settings.DATABASE_URL,
    **get_engine_args(settings.DATABASE_URL)
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
    """Initializes all database tables from registered SQLAlchemy models."""
    Base.metadata.create_all(bind=engine)