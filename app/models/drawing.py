from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Drawing(Base):
    __tablename__ = "drawings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())