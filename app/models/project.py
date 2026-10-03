from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=True)
    images_uploaded = Column(Integer, default=0, nullable=False)
    processing_time = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="COMPLETED", nullable=False)

    width = Column(Float, default=0.0, nullable=False)
    length = Column(Float, default=0.0, nullable=False)
    height = Column(Float, default=0.0, nullable=False)

    ground_area = Column(Float, default=0.0, nullable=False)
    surface_area = Column(Float, default=0.0, nullable=False)
    volume = Column(Float, default=0.0, nullable=False)

    vertices = Column(Integer, default=0, nullable=False)
    triangles = Column(Integer, default=0, nullable=False)

    model_url = Column(String(500), nullable=True)
    report_url = Column(String(500), nullable=True)
    metadata_json = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="projects",
    )
