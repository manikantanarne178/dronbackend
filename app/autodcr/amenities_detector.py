"""
Amenities & Utilities Detector module for AutoDCR.
Automatically detects Solar Panels, Rain Water Harvesting (RWH) Pits, Water Tanks,
Sewage Treatment Plants (STP), Generator Rooms, and Utility Rooms.
"""

from typing import Dict, Any, List
from shapely.geometry import Polygon


class AmenitiesDetector:
    """
    Automatic detection of site services, green amenities, and utility rooms.
    """

    SOLAR_KEYWORDS = ["SOLAR", "SOLAR_PANEL", "PV_ARRAY"]
    RWH_KEYWORDS = ["RWH", "RAIN_WATER", "HARVESTING", "RECHARGE_WELL"]
    TANK_KEYWORDS = ["WATER_TANK", "OHT", "UGT", "SUMP"]
    STP_KEYWORDS = ["STP", "SEWAGE", "TREATMENT_PLANT"]
    DG_KEYWORDS = ["GENERATOR", "DG_ROOM", "TRANSFORMER", "SUBSTATION"]
    UTILITY_KEYWORDS = ["UTILITY", "SERVICE_ROOM", "PUMP_ROOM"]

    @staticmethod
    def detect_amenities(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects solar panels, RWH pits, water tanks, STP, and utility structures.
        """
        entities = parsed_data.get("entities", {})
        polylines = entities.get("polylines", [])

        solar_panels: List[Dict[str, Any]] = []
        rwh_pits: List[Dict[str, Any]] = []
        water_tanks: List[Dict[str, Any]] = []
        stp_units: List[Dict[str, Any]] = []
        generator_rooms: List[Dict[str, Any]] = []
        utility_rooms: List[Dict[str, Any]] = []

        for poly in polylines:
            layer = poly.get("layer", "").upper()
            pts = poly.get("points", [])
            if len(pts) < 3:
                continue

            try:
                p = Polygon(pts)
                info = {
                    "layer": poly.get("layer"),
                    "area": p.area,
                    "bounds": p.bounds,
                    "centroid": [p.centroid.x, p.centroid.y],
                }

                if any(kw in layer for kw in AmenitiesDetector.SOLAR_KEYWORDS):
                    solar_panels.append(info)
                elif any(kw in layer for kw in AmenitiesDetector.RWH_KEYWORDS):
                    rwh_pits.append(info)
                elif any(kw in layer for kw in AmenitiesDetector.TANK_KEYWORDS):
                    water_tanks.append(info)
                elif any(kw in layer for kw in AmenitiesDetector.STP_KEYWORDS):
                    stp_units.append(info)
                elif any(kw in layer for kw in AmenitiesDetector.DG_KEYWORDS):
                    generator_rooms.append(info)
                elif any(kw in layer for kw in AmenitiesDetector.UTILITY_KEYWORDS):
                    utility_rooms.append(info)
            except Exception:
                pass

        return {
            "solar_panels": solar_panels,
            "solar_panel_count": len(solar_panels),
            "total_solar_area": sum(i["area"] for i in solar_panels),
            "rwh_pits": rwh_pits,
            "rwh_pit_count": len(rwh_pits),
            "water_tanks": water_tanks,
            "water_tank_count": len(water_tanks),
            "stp_units": stp_units,
            "stp_count": len(stp_units),
            "generator_rooms": generator_rooms,
            "utility_rooms": utility_rooms,
        }
