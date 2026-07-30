"""
Rule Loader module for AutoDCR.
Loads configurable municipal rule files from app/rules/configs/ dynamically
based on occupancy type (Residential, Commercial, Industrial, Mixed Use, High Rise).
"""

import os
import json
from typing import Dict, Any


class RuleLoader:
    """
    Dynamic rule configuration loader.
    """

    CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rules", "configs")

    @classmethod
    def load_rules_for_occupancy(cls, occupancy: str = "Residential") -> Dict[str, Any]:
        """
        Loads the rule set matching specified occupancy. Falls back to residential.json.
        """
        occ_clean = str(occupancy).lower().strip().replace(" ", "_")
        filename = f"{occ_clean}.json"
        filepath = os.path.join(cls.CONFIG_DIR, filename)

        if not os.path.exists(filepath):
            filepath = os.path.join(cls.CONFIG_DIR, "residential.json")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "zone": "Default",
                "version": "1.0",
                "rules": {
                    "ground_coverage": {"name": "Ground Coverage", "max": 60.0, "reference_code": "DCR-01", "severity": "HIGH", "suggestion": "Reduce footprint."},
                    "fsi": {"name": "FSI", "max": 2.5, "reference_code": "DCR-02", "severity": "CRITICAL", "suggestion": "Reduce total floor area."}
                }
            }
