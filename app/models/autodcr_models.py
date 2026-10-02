"""
SQLAlchemy ORM Database Models for AutoDCR.
Stores Projects, Uploaded Drawings, Spatial Analyses, Rule Validation Results,
Compliance Reports, and Audit Logs with accurate server-generated UTC timestamps.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    JSON,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.models.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class AutoDCRProject(Base):
    """
    Primary database entity representing an AutoDCR Municipal Building Plan Submission.
    """
    __tablename__ = "autodcr_projects"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(100), unique=True, index=True, nullable=False)
    project_code = Column(String(100), index=True, nullable=True)
    name = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, default=0)
    checksum = Column(String(64), nullable=True, index=True)
    zone = Column(String(50), default="Residential", nullable=False)
    status = Column(String(50), default="UPLOADED", nullable=False)
    processing_status = Column(String(50), default="PENDING", nullable=False)
    applicant_name = Column(String(255), nullable=True)
    owner_name = Column(String(255), nullable=True)
    plot_number = Column(String(100), nullable=True)
    survey_number = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Server-generated UTC timestamps - NEVER decided by client
    uploaded_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    drawings = relationship("AutoDCRDrawing", back_populates="project", cascade="all, delete-orphan")
    analysis = relationship("AutoDCRAnalysis", back_populates="project", uselist=False, cascade="all, delete-orphan")
    validations = relationship("RuleValidationResult", back_populates="project", cascade="all, delete-orphan")
    compliance_report = relationship("ComplianceReportModel", back_populates="project", uselist=False, cascade="all, delete-orphan")


class AutoDCRDrawing(Base):
    """
    Stores metadata and extracted CAD/vector geometry for a project drawing file.
    """
    __tablename__ = "autodcr_drawings"

    id = Column(String(100), primary_key=True, index=True)
    project_id = Column(String(100), ForeignKey("autodcr_projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, default=0)
    checksum = Column(String(64), nullable=True)
    parsed_data = Column(JSON, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    project = relationship("AutoDCRProject", back_populates="drawings")


class AutoDCRAnalysis(Base):
    """
    Stores computed spatial metrics, area calculations, height, parking, and detected features.
    """
    __tablename__ = "autodcr_analyses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(100), ForeignKey("autodcr_projects.project_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    detection_results = Column(JSON, nullable=True)
    areas = Column(JSON, nullable=True)
    heights = Column(JSON, nullable=True)
    parking = Column(JSON, nullable=True)
    green_building = Column(JSON, nullable=True)
    accessibility = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    project = relationship("AutoDCRProject", back_populates="analysis")


class RuleValidationResult(Base):
    """
    Individual municipal building bylaw rule evaluation record.
    """
    __tablename__ = "rule_validation_results"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(100), ForeignKey("autodcr_projects.project_id", ondelete="CASCADE"), index=True, nullable=False)
    rule_id = Column(String(100), nullable=True)
    rule_code = Column(String(50), nullable=True)
    rule_name = Column(String(200), nullable=False)
    category = Column(String(100), default="General")
    expected = Column(String(100), nullable=True)
    actual = Column(String(100), nullable=True)
    difference = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False)  # PASS, FAIL, WARNING, INFO
    severity = Column(String(20), default="MEDIUM")  # CRITICAL, HIGH, MEDIUM, LOW
    reason = Column(Text, nullable=True)
    suggestion = Column(Text, nullable=True)
    reference_code = Column(String(100), nullable=True)  # NBC 2016, GDCR, Municipal Bylaws
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    project = relationship("AutoDCRProject", back_populates="validations")


class ComplianceReportModel(Base):
    """
    Comprehensive aggregated municipal scrutiny compliance report.
    """
    __tablename__ = "compliance_reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(100), ForeignKey("autodcr_projects.project_id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    overall_status = Column(String(50), nullable=False)  # APPROVED, REJECTED, REVIEW_REQUIRED
    compliance_score = Column(Float, default=0.0)
    risk_level = Column(String(20), default="Low")
    pass_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    report_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    project = relationship("AutoDCRProject", back_populates="compliance_report")


class AuditLog(Base):
    """
    Audit log for system operations and scrutiny actions.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=True)
    project_id = Column(String(100), index=True, nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(200), nullable=True)
    ip_address = Column(String(50), nullable=True)
    status_code = Column(Integer, default=200)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
