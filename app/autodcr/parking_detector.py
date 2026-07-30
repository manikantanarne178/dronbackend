"""
Parking Detector module for AutoDCR.
Automatically detects parking areas, individual car parking slots, bike parking slots,
accessible (handicapped) parking slots, and driveways based on CAD layers, entity geometry, and text annotations.
"""

from typing import Dict, Any, List
from shapely.geometry import Polygon
from app.geometry.polygon_ops import PolygonOps


class ParkingDetector:
    """
    Automatic parking detection engine.
    """

    PARKING_LAYER_KEYWORDS = ["PARK", "CAR_PARK", "PARKING", "BIKE_PARK", "SLOT", "DRIVEWAY"]

    @staticmethod
    def detect_parking(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects all parking entities and dimensions from normalized parsed drawing data.
        """
        entities = parsed_data.get("entities", {})
        polylines = entities.get("polylines", [])
        texts = parsed_data.get("metadata", {}).get("room_labels", []) + [
            t.get("text", "") for t in entities.get("texts", [])
        ]

        car_slots: List[Dict[str, Any]] = []
        bike_slots: List[Dict[str, Any]] = []
        accessible_slots: List[Dict[str, Any]] = []
        driveways: List[Dict[str, Any]] = []
        total_parking_area = 0.0

        for poly in polylines:
            layer = poly.get("layer", "").upper()
            if any(kw in layer for kw in ParkingDetector.PARKING_LAYER_KEYWORDS):
                pts = poly.get("points", [])
                if len(pts) >= 3:
                    try:
                        p = Polygon(pts)
                        area = p.area
                        bounds = p.bounds
                        width = bounds[2] - bounds[0]
                        height = bounds[3] - bounds[1]

                        # Standard dimensions heuristics (in meters or units)
                        slot_data = {
                            "layer": poly.get("layer"),
                            "area": area,
                            "bounds": bounds,
                            "width": width,
                            "height": height,
                        }

                        if "BIKE" in layer or (area > 1.0 and area < 4.0):
                            bike_slots.append(slot_data)
                        elif "ACCESSIBLE" in layer or "HANDICAP" in layer:
                            accessible_slots.append(slot_data)
                        elif "DRIVEWAY" in layer or area > 35.0:
                            driveways.append(slot_data)
                        else:
                            car_slots.append(slot_data)

                        total_parking_area += area
                    except Exception:
                        pass

        return {
            "car_parking_slots": car_slots,
            "car_parking_count": len(car_slots),
            "bike_parking_slots": bike_slots,
            "bike_parking_count": len(bike_slots),
            "accessible_parking_slots": accessible_slots,
            "accessible_parking_count": len(accessible_slots),
            "driveways": driveways,
            "total_parking_area": total_parking_area,
            "total_slots": len(car_slots) + len(bike_slots) + len(accessible_slots)
        }
