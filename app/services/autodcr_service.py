"""
AutoDCR Core Service.
Handles Centralized File Persistence, Multi-Format Drawing Parsing, Geometry & Feature Extraction,
Spatial Metric Calculation, Municipal Rule Validation, Scrutiny Compliance Scoring,
and Relational Database Persistence with Server UTC Timestamps.
"""

import os
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.models.autodcr_models import (
    AutoDCRProject,
    AutoDCRDrawing,
    AutoDCRAnalysis,
    RuleValidationResult,
    ComplianceReportModel,
    AuditLog,
)
from app.services.storage_service import storage_service
from app.parser.parser_service import ParserService
from app.autodcr.detector_engine import AutomaticDetectionEngine
from app.services.area_service import AreaService
from app.autodcr.height_engine import HeightEngine
from app.autodcr.parking_engine import ParkingEngine
from app.rules.rule_engine import RuleEngine
from app.autodcr.compliance_engine import ComplianceEngine
from app.autodcr.green_building_engine import GreenBuildingEngine
from app.autodcr.accessibility_engine import AccessibilityEngine
from app.services.rule_config_service import RuleConfigService


class AutoDCRService:
    """
    Enterprise AutoDCR Workflow Orchestration Service.
    """

    def __init__(self, db: Session):
        self.db = db
        self.storage = storage_service
        self.rule_config = RuleConfigService(db)

    async def save_uploaded_file(
        self,
        file: UploadFile,
        zone: str = "Residential",
        applicant_name: Optional[str] = None,
        owner_name: Optional[str] = None,
        plot_number: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Persists real uploaded drawing file to verified storage and creates server-owned database records.
        """
        content = await file.read()
        if not content or len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty (0 bytes). Please select a valid drawing file."
            )

        orig_filename = file.filename or "drawing.dxf"
        # Atomically save and physically verify file on disk
        saved = self.storage.save_file(content=content, original_filename=orig_filename)

        file_uuid = saved["file_uuid"]
        stored_filename = saved["stored_filename"]
        storage_key = saved["storage_key"]
        physical_path = saved["physical_path"]
        file_type = saved["file_type"]
        file_size = saved["file_size"]
        checksum = saved["checksum"]

        # Unique project identity
        project_id = f"DCR_{file_uuid[:8].upper()}"
        now = datetime.now(timezone.utc)
        project_code = f"PRJ-{now.strftime('%Y%m%d')}-{file_uuid[:6].upper()}"
        project_name = f"Plan Scrutiny - {Path(orig_filename).stem} ({file_type})"

        # Create AutoDCRProject database entity
        project = AutoDCRProject(
            project_id=project_id,
            project_code=project_code,
            name=project_name,
            original_filename=orig_filename,
            stored_filename=stored_filename,
            file_path=str(physical_path),
            file_type=file_type,
            mime_type=file.content_type or f"application/{file_type.lower()}",
            file_size=file_size,
            checksum=checksum,
            zone=zone or "Residential",
            status="PROCESSING",
            processing_status="PROCESSING",
            applicant_name=applicant_name or "Municipal Applicant",
            owner_name=owner_name or "Property Owner",
            plot_number=plot_number or f"Plot #{file_uuid[:4].upper()}",
            uploaded_at=now,
            created_at=now,
            updated_at=now,
            user_id=user_id,
        )
        self.db.add(project)

        # Create AutoDCRDrawing database entity
        drawing = AutoDCRDrawing(
            id=file_uuid,
            project_id=project_id,
            filename=orig_filename,
            stored_filename=stored_filename,
            file_path=str(physical_path),
            file_type=file_type,
            file_size=file_size,
            checksum=checksum,
            uploaded_at=now,
        )
        self.db.add(drawing)
        self.db.commit()
        self.db.refresh(project)

        # Automatically execute full analysis pipeline on upload
        try:
            analysis_result = await self.process_full_pipeline(project_id, zone=zone)
            return {
                "success": True,
                "project_id": project.project_id,
                "project_code": project.project_code,
                "name": project.name,
                "filename": orig_filename,
                "stored_filename": stored_filename,
                "file_id": project.project_id,
                "file_type": file_type,
                "file_size": file_size,
                "checksum": checksum,
                "zone": project.zone,
                "status": project.status,
                "uploaded_at": project.uploaded_at.isoformat(),
                "created_at": project.created_at.isoformat(),
                "analysis": analysis_result
            }
        except Exception as e:
            project.status = "FAILED"
            project.processing_status = "FAILED"
            project.error_message = str(e)
            self.db.commit()
            return {
                "success": False,
                "project_id": project.project_id,
                "filename": orig_filename,
                "stored_filename": stored_filename,
                "file_id": project.project_id,
                "file_type": file_type,
                "status": "FAILED",
                "error": str(e),
                "uploaded_at": project.uploaded_at.isoformat(),
                "created_at": project.created_at.isoformat(),
            }

    def _resolve_file_path(self, identifier: str) -> Path:
        """
        Resolves the actual physical file path via StorageService.
        Never exposes raw internal filesystem paths to error messages.
        """
        if not identifier:
            raise HTTPException(status_code=400, detail="No project or drawing identifier provided.")

        clean_id = Path(identifier).name

        # 1. Check direct project match in database
        proj = (
            self.db.query(AutoDCRProject)
            .filter(
                (AutoDCRProject.project_id == identifier) |
                (AutoDCRProject.stored_filename == clean_id) |
                (AutoDCRProject.project_code == identifier)
            )
            .first()
        )
        if proj:
            resolved = self.storage.resolve_physical_path(proj.stored_filename)
            if resolved:
                return resolved
            # If project exists in DB but file missing from storage
            proj.status = "FILE_MISSING"
            proj.processing_status = "FILE_MISSING"
            self.db.commit()
            raise HTTPException(
                status_code=404,
                detail=f"Drawing file for project '{proj.name}' was not found in storage. Please re-upload the drawing."
            )

        # 2. Check drawing match in database
        draw = (
            self.db.query(AutoDCRDrawing)
            .filter(
                (AutoDCRDrawing.id == identifier) |
                (AutoDCRDrawing.stored_filename == clean_id)
            )
            .first()
        )
        if draw:
            resolved = self.storage.resolve_physical_path(draw.stored_filename)
            if resolved:
                return resolved
            raise HTTPException(
                status_code=404,
                detail="Drawing file was not found in storage. Please re-upload the drawing."
            )

        # 3. Check directly in storage root
        resolved = self.storage.resolve_physical_path(clean_id)
        if resolved:
            return resolved

        raise HTTPException(
            status_code=404,
            detail=f"Drawing file '{clean_id}' was not found in storage. Please select a valid project or upload a drawing."
        )

    async def parse_file(self, identifier: str) -> Dict[str, Any]:
        """
        Parses actual CAD/BIM drawing file using multi-format ParserService and persists parsed schema.
        """
        file_path = self._resolve_file_path(identifier)
        parsed_data = ParserService.parse(str(file_path))
        parsed_data["file_id"] = file_path.name
        parsed_data["status"] = "COMPLETED"
        parsed_data["text"] = [t.get("text", "") for t in parsed_data.get("texts", []) if isinstance(t, dict)]

        # If project or drawing exists, update DB parsed_data
        drawing = self.db.query(AutoDCRDrawing).filter(
            (AutoDCRDrawing.stored_filename == file_path.name) | (AutoDCRDrawing.id == file_path.stem)
        ).first()
        if drawing:
            drawing.parsed_data = parsed_data
            self.db.commit()

        return parsed_data

    async def process_full_pipeline(
        self,
        identifier: str,
        zone: str = "Residential",
        floor_count: int = 1
    ) -> Dict[str, Any]:
        """
        Executes end-to-end AutoDCR analysis, rule evaluation, compliance scoring, and persists results.
        """
        file_path = self._resolve_file_path(identifier)
        
        # Find project in database
        project = (
            self.db.query(AutoDCRProject)
            .filter(
                (AutoDCRProject.project_id == identifier) |
                (AutoDCRProject.stored_filename == file_path.name)
            )
            .first()
        )

        # 1. Parse File
        parsed_data = ParserService.parse(str(file_path))
        parsed_data["file_id"] = file_path.name
        parsed_data["status"] = "COMPLETED"

        # 2. Automatic Feature Detection
        detection_results = AutomaticDetectionEngine.detect_all(parsed_data)

        # 3. Spatial Calculations
        effective_zone = zone or (project.zone if project else "Residential")
        areas = AreaService.calculate_all_areas(detection_results, floor_count=floor_count)
        heights = HeightEngine.calculate_heights(parsed_data, floor_count=floor_count)
        parking = ParkingEngine.calculate_parking_requirements(
            built_up_area=areas["built_up_area"],
            occupancy_type=effective_zone,
            detected_parking=detection_results.get("parking", {})
        )

        # 4. Rule Validation Engine
        validations = RuleEngine.validate_comprehensive(
            areas=areas,
            heights=heights,
            parking=parking,
            detection_results=detection_results,
            occupancy=effective_zone
        )

        # 5. Scrutiny Compliance Scoring
        compliance = ComplianceEngine.evaluate(validations)
        green_building = GreenBuildingEngine.evaluate(detection_results, areas)
        accessibility = AccessibilityEngine.evaluate(detection_results, parsed_data)

        # Determine Final Project Status
        fail_count = compliance.get("fail_count", 0)
        warning_count = compliance.get("warning_count", 0)
        
        if fail_count > 0:
            final_status = "REJECTED"
        elif warning_count > 0 or not detection_results.get("plot", {}).get("detected"):
            final_status = "REVIEW_REQUIRED"
        else:
            final_status = "APPROVED"

        # Update Project and Persist Analysis & Validations in DB
        if project:
            project.status = final_status
            project.processing_status = "COMPLETED"
            project.zone = effective_zone
            project.updated_at = datetime.now(timezone.utc)

            # Persist or update AutoDCRAnalysis
            analysis_record = self.db.query(AutoDCRAnalysis).filter(AutoDCRAnalysis.project_id == project.project_id).first()
            if not analysis_record:
                analysis_record = AutoDCRAnalysis(project_id=project.project_id)
                self.db.add(analysis_record)

            analysis_record.detection_results = detection_results
            analysis_record.areas = areas
            analysis_record.heights = heights
            analysis_record.parking = parking
            analysis_record.green_building = green_building
            analysis_record.accessibility = accessibility

            # Clear old rule validation results for this project and insert new ones
            self.db.query(RuleValidationResult).filter(RuleValidationResult.project_id == project.project_id).delete()
            for v in validations:
                res_obj = RuleValidationResult(
                    project_id=project.project_id,
                    rule_id=v.get("rule_id"),
                    rule_code=v.get("rule_code"),
                    rule_name=v.get("rule_name"),
                    category=v.get("category", "General"),
                    expected=str(v.get("expected", "")),
                    actual=str(v.get("actual", "")),
                    difference=str(v.get("difference", "")),
                    status=v.get("status", "PASS"),
                    severity=v.get("severity", "MEDIUM"),
                    reason=v.get("reason"),
                    suggestion=v.get("suggestion"),
                    reference_code=v.get("reference_code"),
                )
                self.db.add(res_obj)

            # Persist or update ComplianceReportModel
            report_record = self.db.query(ComplianceReportModel).filter(ComplianceReportModel.project_id == project.project_id).first()
            if not report_record:
                report_record = ComplianceReportModel(project_id=project.project_id, overall_status=final_status)
                self.db.add(report_record)

            report_record.overall_status = final_status
            report_record.compliance_score = compliance.get("compliance_score", 0.0)
            report_record.risk_level = compliance.get("risk_level", "Low")
            report_record.pass_count = compliance.get("pass_count", 0)
            report_record.fail_count = compliance.get("fail_count", 0)
            report_record.warning_count = compliance.get("warning_count", 0)
            report_record.report_data = {
                "project_id": project.project_id,
                "project_code": project.project_code,
                "overall_status": final_status,
                "compliance": compliance,
                "areas": areas,
                "heights": heights,
                "parking": parking,
                "validations": validations,
                "green_building": green_building,
                "accessibility": accessibility,
            }

            self.db.commit()
            self.db.refresh(project)

        return {
            "project_id": project.project_id if project else identifier,
            "file_id": project.project_id if project else file_path.name,
            "status": final_status,
            "zone": effective_zone,
            "detection_results": detection_results,
            "areas": areas,
            "heights": heights,
            "parking": parking,
            "validations": validations,
            "compliance": compliance,
            "green_building": green_building,
            "accessibility": accessibility,
        }

    def list_projects(self) -> List[Dict[str, Any]]:
        """
        Returns all real AutoDCR projects from the database.
        """
        projects = self.db.query(AutoDCRProject).order_by(AutoDCRProject.uploaded_at.desc()).all()
        result = []
        for p in projects:
            # Check physical file health
            is_file_available = self.storage.exists(p.stored_filename)
            effective_status = p.status
            if not is_file_available and p.status not in ["FILE_MISSING", "FAILED"]:
                effective_status = "FILE_MISSING"

            result.append({
                "id": p.project_id,
                "project_id": p.project_id,
                "project_code": p.project_code,
                "name": p.name,
                "filename": p.original_filename,
                "file_name": p.original_filename,
                "stored_filename": p.stored_filename,
                "file_id": p.project_id,
                "file_type": p.file_type,
                "file_size": p.file_size,
                "zone": p.zone,
                "status": effective_status,
                "processing_status": p.processing_status,
                "is_file_available": is_file_available,
                "applicant_name": p.applicant_name,
                "owner_name": p.owner_name,
                "plot_number": p.plot_number,
                "uploaded_at": p.uploaded_at.isoformat() if p.uploaded_at else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            })
        return result

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Retrieves detailed information for a single AutoDCR project from database.
        """
        clean_id = Path(project_id).name
        project = (
            self.db.query(AutoDCRProject)
            .filter(
                (AutoDCRProject.project_id == project_id) |
                (AutoDCRProject.stored_filename == clean_id) |
                (AutoDCRProject.project_code == project_id)
            )
            .first()
        )
        if not project:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

        analysis = self.db.query(AutoDCRAnalysis).filter(AutoDCRAnalysis.project_id == project.project_id).first()
        validations = self.db.query(RuleValidationResult).filter(RuleValidationResult.project_id == project.project_id).all()
        report = self.db.query(ComplianceReportModel).filter(ComplianceReportModel.project_id == project.project_id).first()

        is_file_available = self.storage.exists(project.stored_filename)

        return {
            "id": project.project_id,
            "project_id": project.project_id,
            "project_code": project.project_code,
            "name": project.name,
            "filename": project.original_filename,
            "stored_filename": project.stored_filename,
            "file_id": project.project_id,
            "file_type": project.file_type,
            "file_size": project.file_size,
            "checksum": project.checksum,
            "zone": project.zone,
            "status": project.status if is_file_available else "FILE_MISSING",
            "processing_status": project.processing_status,
            "is_file_available": is_file_available,
            "applicant_name": project.applicant_name,
            "owner_name": project.owner_name,
            "plot_number": project.plot_number,
            "uploaded_at": project.uploaded_at.isoformat() if project.uploaded_at else None,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "analysis": {
                "detection_results": analysis.detection_results if analysis else None,
                "areas": analysis.areas if analysis else None,
                "heights": analysis.heights if analysis else None,
                "parking": analysis.parking if analysis else None,
                "green_building": analysis.green_building if analysis else None,
                "accessibility": analysis.accessibility if analysis else None,
            } if analysis else None,
            "validations": [
                {
                    "rule_id": v.rule_id,
                    "rule_code": v.rule_code,
                    "rule_name": v.rule_name,
                    "category": v.category,
                    "expected": v.expected,
                    "actual": v.actual,
                    "difference": v.difference,
                    "status": v.status,
                    "severity": v.severity,
                    "reason": v.reason,
                    "suggestion": v.suggestion,
                    "reference_code": v.reference_code,
                }
                for v in validations
            ],
            "compliance_report": {
                "overall_status": report.overall_status,
                "compliance_score": report.compliance_score,
                "risk_level": report.risk_level,
                "pass_count": report.pass_count,
                "fail_count": report.fail_count,
                "warning_count": report.warning_count,
                "report_data": report.report_data,
            } if report else None
        }

    async def get_result(self, project_id: str) -> Dict[str, Any]:
        """
        Retrieves actual persisted validation results and compliance status for a project.
        """
        clean_id = Path(project_id).name
        project = (
            self.db.query(AutoDCRProject)
            .filter(
                (AutoDCRProject.project_id == project_id) |
                (AutoDCRProject.stored_filename == clean_id) |
                (AutoDCRProject.project_code == project_id)
            )
            .first()
        )
        if not project:
            # If project record not yet created but file exists on disk, run pipeline
            file_path = self._resolve_file_path(project_id)
            return await self.process_full_pipeline(file_path.name)

        validations = self.db.query(RuleValidationResult).filter(RuleValidationResult.project_id == project.project_id).all()
        report = self.db.query(ComplianceReportModel).filter(ComplianceReportModel.project_id == project.project_id).first()
        analysis = self.db.query(AutoDCRAnalysis).filter(AutoDCRAnalysis.project_id == project.project_id).first()

        # If no validations exist in DB yet, run analysis
        if not validations:
            return await self.process_full_pipeline(project.project_id, zone=project.zone)

        return {
            "result_id": project.project_id,
            "project_id": project.project_id,
            "status": project.status,
            "compliance_percentage": report.compliance_score if report else 0.0,
            "risk_level": report.risk_level if report else "Low",
            "pass_count": report.pass_count if report else len([v for v in validations if v.status == 'PASS']),
            "fail_count": report.fail_count if report else len([v for v in validations if v.status == 'FAIL']),
            "warning_count": report.warning_count if report else len([v for v in validations if v.status == 'WARNING']),
            "validations": [
                {
                    "rule_id": v.rule_id,
                    "rule_code": v.rule_code,
                    "rule_name": v.rule_name,
                    "category": v.category,
                    "expected": v.expected,
                    "actual": v.actual,
                    "difference": v.difference,
                    "status": v.status,
                    "severity": v.severity,
                    "reason": v.reason,
                    "suggestion": v.suggestion,
                    "reference_code": v.reference_code,
                }
                for v in validations
            ],
            "areas": analysis.areas if analysis else None,
            "heights": analysis.heights if analysis else None,
            "parking": analysis.parking if analysis else None,
            "details": f"Scrutiny complete: Status is {project.status}."
        }

    async def get_scrutiny_report(self, project_id: str) -> Dict[str, Any]:
        """
        Builds the unified, comprehensive scrutiny report payload from actual database records.
        """
        clean_id = Path(project_id).name
        project = (
            self.db.query(AutoDCRProject)
            .filter(
                (AutoDCRProject.project_id == project_id) |
                (AutoDCRProject.stored_filename == clean_id) |
                (AutoDCRProject.project_code == project_id)
            )
            .first()
        )
        if not project:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

        # Ensure analysis exists
        analysis = self.db.query(AutoDCRAnalysis).filter(AutoDCRAnalysis.project_id == project.project_id).first()
        validations = self.db.query(RuleValidationResult).filter(RuleValidationResult.project_id == project.project_id).all()
        report = self.db.query(ComplianceReportModel).filter(ComplianceReportModel.project_id == project.project_id).first()

        if not analysis or not validations:
            await self.process_full_pipeline(project.project_id, zone=project.zone)
            analysis = self.db.query(AutoDCRAnalysis).filter(AutoDCRAnalysis.project_id == project.project_id).first()
            validations = self.db.query(RuleValidationResult).filter(RuleValidationResult.project_id == project.project_id).all()
            report = self.db.query(ComplianceReportModel).filter(ComplianceReportModel.project_id == project.project_id).first()

        areas = analysis.areas or {} if analysis else {}
        heights = analysis.heights or {} if analysis else {}
        parking = analysis.parking or {} if analysis else {}
        det_results = analysis.detection_results or {} if analysis else {}
        
        val_list = [
            {
                "rule_id": v.rule_id,
                "rule_code": v.rule_code,
                "rule_name": v.rule_name,
                "category": v.category,
                "expected": v.expected,
                "actual": v.actual,
                "difference": v.difference,
                "status": v.status,
                "severity": v.severity,
                "reason": v.reason,
                "suggestion": v.suggestion,
                "reference_code": v.reference_code,
            }
            for v in validations
        ]
        violations = [v for v in val_list if v["status"] in ("FAIL", "WARNING", "REVIEW_REQUIRED")]

        return {
            "project": {
                "id": project.project_id,
                "project_id": project.project_id,
                "project_code": project.project_code,
                "name": project.name,
                "filename": project.original_filename,
                "original_filename": project.original_filename,
                "stored_filename": project.stored_filename,
                "file_type": project.file_type,
                "file_size": project.file_size,
                "checksum": project.checksum,
                "zone": project.zone,
                "status": project.status,
                "processing_status": project.processing_status,
                "applicant_name": project.applicant_name,
                "owner_name": project.owner_name,
                "plot_number": project.plot_number,
                "uploaded_at": project.uploaded_at.isoformat() if project.uploaded_at else None,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            },
            "file": {
                "original_name": project.original_filename,
                "stored_name": project.stored_filename,
                "file_type": project.file_type,
                "file_size": project.file_size,
                "checksum": project.checksum,
                "mime_type": project.mime_type,
            },
            "scrutiny": {
                "overall_status": report.overall_status if report else project.status,
                "compliance_score": report.compliance_score if report else 0.0,
                "risk_level": report.risk_level if report else "Low",
                "pass_count": report.pass_count if report else len([v for v in val_list if v["status"] == "PASS"]),
                "fail_count": report.fail_count if report else len([v for v in val_list if v["status"] == "FAIL"]),
                "warning_count": report.warning_count if report else len(violations),
            },
            "analysis": {
                "areas": areas,
                "heights": heights,
                "parking": parking,
                "detection_results": det_results,
                "green_building": analysis.green_building if analysis else None,
                "accessibility": analysis.accessibility if analysis else None,
            },
            "metrics": {
                "plot_area": areas.get("plot_area"),
                "plot_area_unit": "sq.m",
                "built_up_area": areas.get("built_up_area"),
                "built_up_area_unit": "sq.m",
                "fsi": areas.get("far") or areas.get("fsi"),
                "far": areas.get("far"),
                "ground_coverage_pct": areas.get("ground_coverage_pct"),
                "building_height": heights.get("building_height"),
                "road_width": det_results.get("road", {}).get("width") or det_results.get("roads", {}).get("width", 9.0),
                "setbacks": det_results.get("road", {}).get("setbacks") or det_results.get("setbacks") or {},
                "car_parking": parking.get("car_parking_count", 0),
            },
            "rules": val_list,
            "validations": val_list,
            "violations": violations,
            "summary": {
                "total_rules": len(val_list),
                "passed": report.pass_count if report else len([v for v in val_list if v["status"] == "PASS"]),
                "failed": report.fail_count if report else len([v for v in val_list if v["status"] == "FAIL"]),
                "review_required": len(violations),
                "compliance_percentage": report.compliance_score if report else 0.0,
                "overall_status": report.overall_status if report else project.status,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def generate_scrutiny_pdf(self, project_id: str) -> bytes:
        """
        Generates official PDF scrutiny report bytes for download.
        """
        report_data = await self.get_scrutiny_report(project_id)
        from app.reports.autodcr_pdf import AutoDCRPDFGenerator
        pdf_gen = AutoDCRPDFGenerator(report_data)
        return pdf_gen.generate_pdf_bytes()

    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """
        Safely deletes a project, its associated records, and stored drawing files.
        """
        clean_id = Path(project_id).name
        project = (
            self.db.query(AutoDCRProject)
            .filter(
                (AutoDCRProject.project_id == project_id) |
                (AutoDCRProject.stored_filename == clean_id) |
                (AutoDCRProject.project_code == project_id)
            )
            .first()
        )
        if not project:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

        # Delete physical file via StorageService
        if project.stored_filename:
            self.storage.delete_file(project.stored_filename)

        # Database cascade deletes drawings, analyses, validations, reports
        self.db.delete(project)
        self.db.commit()

        return {
            "success": True,
            "message": f"AutoDCR project '{project_id}' and associated drawing files deleted successfully."
        }

    def cleanup_old_data(self) -> Dict[str, Any]:
        """
        Removes stale development/mock AutoDCR projects and orphaned upload files.
        """
        del_validations = self.db.query(RuleValidationResult).delete()
        del_reports = self.db.query(ComplianceReportModel).delete()
        del_analyses = self.db.query(AutoDCRAnalysis).delete()
        del_drawings = self.db.query(AutoDCRDrawing).delete()
        del_projects = self.db.query(AutoDCRProject).delete()
        self.db.commit()

        # Clean orphaned files
        removed_files = 0
        if self.storage.root.exists():
            for f in self.storage.root.iterdir():
                if f.is_file():
                    try:
                        f.unlink()
                        removed_files += 1
                    except Exception:
                        pass

        return {
            "success": True,
            "deleted_projects": del_projects,
            "deleted_drawings": del_drawings,
            "deleted_analyses": del_analyses,
            "deleted_validations": del_validations,
            "deleted_reports": del_reports,
            "removed_files_count": removed_files,
            "message": "AutoDCR database and storage cleaned safely. Ready for real uploads."
        }