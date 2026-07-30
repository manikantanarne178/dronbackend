"""
SQLAlchemy ORM Database Models for AutoDCR.
Stores Validation Results, Compliance Reports, Audit Logs, and Rule Versioning history.
"""

import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, ForeignKey
from app.models.base import Base


class RuleValidationResult(Base):
    __tablename__ = "rule_validation_results"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(100), index=True, nullable=False)
    rule_name = Column(String(200), nullable=False)
    expected = Column(String(100))
    actual = Column(String(100))
    status = Column(String(20), nullable=False)  # PASS, FAIL, WARNING, INFO
    severity = Column(String(20), default="MEDIUM")
    reason = Column(Text)
    suggestion = Column(Text)
    reference_code = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ComplianceReportModel(Base):
    __tablename__ = "compliance_reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(100), unique=True, index=True, nullable=False)
    overall_status = Column(String(20), nullable=False)
    compliance_score = Column(Float, default=0.0)
    risk_level = Column(String(20), default="Low")
    pass_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    report_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(200))
    ip_address = Column(String(50))
    status_code = Column(Integer, default=200)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
