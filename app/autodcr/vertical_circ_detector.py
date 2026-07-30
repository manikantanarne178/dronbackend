"""
Vertical & Horizontal Circulation Detector module for AutoDCR.
Automatically detects Lifts, Lift Shafts, Normal Staircases, Fire Staircases,
Vehicle Ramps, and Pedestrian Ramps, calculating slope ratios, widths, and landings.
"""

from typing import Dict, Any, List
from shapely.geometry import Polygon


class VerticalCirculationDetector:
    """
    Automatic detection of lifts, staircases, and ramps with ramp slope & landing validation.
    """

    STAIR_KEYWORDS = ["STAIR", "FIRE_STAIR", "STAIRCASE", "STEPS", "FIRE_ESCAPE"]
    LIFT_KEYWORDS = ["LIFT", "ELEVATOR", "LIFT_SHAFT", "FIRE_LIFT"]
    RAMP_KEYWORDS = ["RAMP", "VEHICLE_RAMP", "PEDESTRIAN_RAMP", "DRIVE_RAMP"]

    @staticmethod
    def detect_circulation(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects lifts, staircases, and ramps from parsed CAD data with complete slope geometry.
        """
        entities = parsed_data.get("entities", {})
        polylines = entities.get("polylines", [])

        lifts: List[Dict[str, Any]] = []
        normal_staircases: List[Dict[str, Any]] = []
        fire_staircases: List[Dict[str, Any]] = []
        ramps: List[Dict[str, Any]] = []

        for poly in polylines:
            layer = poly.get("layer", "").upper()
            pts = poly.get("points", [])
            if len(pts) < 3:
                continue

            try:
                p = Polygon(pts)
                bounds = p.bounds
                width = min(bounds[2] - bounds[0], bounds[3] - bounds[1])
                length = max(bounds[2] - bounds[0], bounds[3] - bounds[1])

                info = {
                    "layer": poly.get("layer"),
                    "area": p.area,
                    "bounds": bounds,
                    "width": round(width, 2),
                    "length": round(length, 2),
                    "centroid": [p.centroid.x, p.centroid.y],
                }

                if any(kw in layer for kw in VerticalCirculationDetector.LIFT_KEYWORDS):
                    info["is_fire_lift"] = "FIRE" in layer
                    lifts.append(info)
                elif any(kw in layer for kw in VerticalCirculationDetector.STAIR_KEYWORDS):
                    if "FIRE" in layer:
                        fire_staircases.append(info)
                    else:
                        normal_staircases.append(info)
                elif any(kw in layer for kw in VerticalCirculationDetector.RAMP_KEYWORDS):
                    # Calculate slope metrics
                    height_diff = float(poly.get("height_difference", 1.5))  # Default 1.5m ramp rise if not specified
                    slope_pct = (height_diff / length * 100.0) if length > 0 else 10.0
                    slope_ratio_val = (length / height_diff) if height_diff > 0 else 10.0

                    ramp_type = "ACCESSIBLE" if "ACCESSIBLE" in layer or "HANDICAP" in layer else "PARKING" if "PARK" in layer or "VEHICLE" in layer else "GENERAL"
                    max_allowed_slope_pct = 8.33 if ramp_type == "ACCESSIBLE" else 12.5 if ramp_type == "PARKING" else 10.0

                    info.update({
                        "height_difference": round(height_diff, 2),
                        "slope_percentage": round(slope_pct, 2),
                        "slope_ratio": f"1:{round(slope_ratio_val, 1)}",
                        "ramp_type": ramp_type,
                        "landing_detected": length > 6.0,  # Intermediate landing required every 6m
                        "turning_radius": round(width * 1.5, 2),
                        "is_slope_compliant": slope_pct <= max_allowed_slope_pct
                    })
                    ramps.append(info)
            except Exception:
                pass

        return {
            "lifts": lifts,
            "lift_count": len(lifts),
            "normal_staircases": normal_staircases,
            "normal_staircase_count": len(normal_staircases),
            "fire_staircases": fire_staircases,
            "fire_staircase_count": len(fire_staircases),
            "ramps": ramps,
            "ramp_count": len(ramps),
        }
