"""
Rule Engine module for AutoDCR.
Evaluates municipal building control rules and returns structured validation objects.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.rules.plot import PlotRule
from app.rules.fsi import FSIRule
from app.rules.coverage import CoverageRule
from app.rules.setback import SetbackRule
from app.services.rule_config_service import RuleConfigService
from app.autodcr.rule_loader import RuleLoader


class RuleEngine:

    @staticmethod
    def validate(plot, building, db: Session):
        config = RuleConfigService(db)
        rules = [
            PlotRule.check(plot),
            FSIRule.check(plot, building, config),
            CoverageRule.check(plot, building, config),
            SetbackRule.check(plot, building, config),
        ]

        passed = sum(1 for r in rules if r["status"] == "PASS")
        failed = sum(1 for r in rules if r["status"] == "FAIL")
        warning = sum(1 for r in rules if r["status"] == "WARNING")

        return {
            "summary": {
                "total": len(rules),
                "passed": passed,
                "failed": failed,
                "warning": warning
            },
            "rules": rules
        }

    @staticmethod
    def validate_comprehensive(
        areas: Dict[str, float],
        heights: Dict[str, float],
        parking: Dict[str, Any],
        detection_results: Dict[str, Any],
        occupancy: str = "Residential"
    ) -> List[Dict[str, Any]]:
        """
        Runs comprehensive rule validation against configurable rule sets.
        """
        rule_config = RuleLoader.load_rules_for_occupancy(occupancy)
        rules_def = rule_config.get("rules", {})
        validation_results: List[Dict[str, Any]] = []

        # 1. Ground Coverage
        gc_def = rules_def.get("ground_coverage", {})
        max_gc = float(gc_def.get("max", 65.0))
        act_gc = round(areas.get("ground_coverage_pct", 0.0), 2)
        gc_pass = act_gc <= max_gc
        validation_results.append({
            "rule_name": gc_def.get("name", "Ground Coverage Percentage"),
            "expected": f"<= {max_gc}%",
            "actual": f"{act_gc}%",
            "status": "PASS" if gc_pass else "FAIL",
            "severity": gc_def.get("severity", "HIGH"),
            "reason": f"Ground coverage is {act_gc}%, maximum allowed is {max_gc}%." if not gc_pass else "Ground coverage compliant.",
            "suggestion": gc_def.get("suggestion", "Reduce building footprint."),
            "reference_code": gc_def.get("reference_code", "DCR-01")
        })

        # 2. FSI / FAR
        fsi_def = rules_def.get("fsi", {})
        max_fsi = float(fsi_def.get("max", 2.5))
        act_fsi = round(areas.get("far", 0.0), 2)
        fsi_pass = act_fsi <= max_fsi
        validation_results.append({
            "rule_name": fsi_def.get("name", "Floor Space Index (FSI)"),
            "expected": f"<= {max_fsi}",
            "actual": f"{act_fsi}",
            "status": "PASS" if fsi_pass else "FAIL",
            "severity": fsi_def.get("severity", "CRITICAL"),
            "reason": f"FSI is {act_fsi}, maximum allowed is {max_fsi}." if not fsi_pass else "FSI compliant.",
            "suggestion": fsi_def.get("suggestion", "Reduce built-up area."),
            "reference_code": fsi_def.get("reference_code", "DCR-02")
        })

        # 3. Building Height
        h_def = rules_def.get("building_height", {})
        max_h = float(h_def.get("max", 18.0))
        act_h = round(heights.get("building_height", 0.0), 2)
        h_pass = act_h <= max_h
        validation_results.append({
            "rule_name": h_def.get("name", "Building Height"),
            "expected": f"<= {max_h}m",
            "actual": f"{act_h}m",
            "status": "PASS" if h_pass else "FAIL",
            "severity": h_def.get("severity", "CRITICAL"),
            "reason": f"Height is {act_h}m, maximum allowed is {max_h}m." if not h_pass else "Building height compliant.",
            "suggestion": h_def.get("suggestion", "Reduce height."),
            "reference_code": h_def.get("reference_code", "DCR-03")
        })

        # 4. Parking Compliance
        pk_pass = parking.get("is_parking_compliant", True)
        validation_results.append({
            "rule_name": "Parking Provision",
            "expected": f"{parking.get('required_car_parking', 0)} car slots",
            "actual": f"{parking.get('available_car_parking', 0)} car slots",
            "status": "PASS" if pk_pass else "FAIL",
            "severity": "HIGH",
            "reason": "; ".join(parking.get("parking_violations", [])) if not pk_pass else "Parking provision compliant.",
            "suggestion": "Add required parking slots.",
            "reference_code": "DCR-04"
        })

        # 5. Rain Water Harvesting
        rwh_count = detection_results.get("amenities", {}).get("rwh_pit_count", 0)
        validation_results.append({
            "rule_name": "Rain Water Harvesting Pit",
            "expected": ">= 1 pit",
            "actual": f"{rwh_count} pits",
            "status": "PASS" if rwh_count >= 1 else "WARNING",
            "severity": "MEDIUM",
            "reason": "Rain Water Harvesting pit recommended/mandatory." if rwh_count < 1 else "RWH pit provided.",
            "suggestion": "Designate RWH pit on CAD layout.",
            "reference_code": "DCR-05"
        })

        return validation_results