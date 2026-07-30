"""
Compliance Engine module for AutoDCR.
Calculates overall compliance score %, pass/fail/warning counts, risk level,
and generates actionable municipal recommendations based on rule validations.
"""

from typing import Dict, Any, List


class ComplianceEngine:
    """
    Municipal compliance scoring engine.
    """

    @staticmethod
    def evaluate(validations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates compliance score %, pass/fail counts, risk level, and recommendations.
        """
        total = len(validations)
        if total == 0:
            return {
                "overall_status": "PASS",
                "compliance_score": 100.0,
                "overall_compliance_pct": 100.0,
                "pass_count": 0,
                "fail_count": 0,
                "warning_count": 0,
                "info_count": 0,
                "risk_level": "Low",
                "recommendations": []
            }

        pass_count = sum(1 for v in validations if v["status"] == "PASS")
        fail_count = sum(1 for v in validations if v["status"] == "FAIL")
        warning_count = sum(1 for v in validations if v["status"] == "WARNING")
        info_count = sum(1 for v in validations if v["status"] == "INFO")

        # Score calculation: PASS = 1.0, WARNING = 0.5, FAIL = 0.0
        points = (pass_count * 1.0) + (warning_count * 0.5)
        score_pct = round((points / total) * 100.0, 2)

        # Risk level determination
        if fail_count > 2 or score_pct < 70.0:
            risk_level = "High"
            overall_status = "FAIL"
        elif fail_count > 0 or warning_count > 1 or score_pct < 90.0:
            risk_level = "Medium"
            overall_status = "WARNING" if fail_count == 0 else "FAIL"
        else:
            risk_level = "Low"
            overall_status = "PASS"

        recommendations = []
        for v in validations:
            if v["status"] in ["FAIL", "WARNING"]:
                recommendations.append(f"[{v['severity']}] {v['rule_name']}: {v['suggestion']} (Ref: {v['reference_code']})")

        return {
            "overall_status": overall_status,
            "compliance_score": score_pct,
            "overall_compliance_pct": score_pct,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "risk_level": risk_level,
            "recommendations": recommendations,
        }
