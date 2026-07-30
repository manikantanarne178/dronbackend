"""
Master Automatic Detection Engine for AutoDCR.
Orchestrates spatial analysis across CAD layers and geometric entities
to detect Plot Boundaries, Buildings, Roads, Parking, Vertical Circulation,
Floor Projections, Open Spaces, and Site Amenities automatically without manual selection.
"""

from typing import Dict, Any, List
from app.autodcr.parking_detector import ParkingDetector
from app.autodcr.vertical_circ_detector import VerticalCirculationDetector
from app.autodcr.floor_detector import FloorDetector
from app.autodcr.amenities_detector import AmenitiesDetector
from app.services.plot_detector import PlotDetector
from app.services.building_detector import BuildingDetector
from app.services.road_detection import RoadDetector
from app.geometry.polygon_ops import PolygonOps


class AutomaticDetectionEngine:
    """
    Unified automatic detection engine for AutoDCR municipal approval workflow.
    """

    @staticmethod
    def detect_all(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs complete automatic detection suite on normalized CAD data.
        """
        entities = parsed_data.get("entities", {})
        polylines = entities.get("polylines", [])

        # Detect closed polygons using PolygonOps
        raw_polygons = PolygonOps.detect_closed_polygons(polylines)
        formatted_polys = []
        for poly in raw_polygons:
            formatted_polys.append({
                "points": list(poly.exterior.coords),
                "area": poly.area,
                "centroid": [poly.centroid.x, poly.centroid.y]
            })

        # Run individual sub-detectors
        plot_info = PlotDetector.detect(formatted_polys) if formatted_polys else None
        building_info = BuildingDetector.detect(formatted_polys, plot_info) if formatted_polys and plot_info else []
        road_info = RoadDetector.detect(plot_info) if plot_info else {}


        parking_data = ParkingDetector.detect_parking(parsed_data)
        circulation_data = VerticalCirculationDetector.detect_circulation(parsed_data)
        floor_data = FloorDetector.detect_floor_elements(parsed_data)
        amenities_data = AmenitiesDetector.detect_amenities(parsed_data)

        # Combine into complete detection result
        detection_result = {
            "plot": plot_info,
            "buildings": building_info,
            "roads": road_info,
            "parking": parking_data,
            "circulation": circulation_data,
            "floor_elements": floor_data,
            "amenities": amenities_data,
            "metadata": parsed_data.get("metadata", {}),
            "is_corner_plot": len(road_info.get("roads", [])) > 1 if isinstance(road_info, dict) else False,
            "total_polygons_detected": len(formatted_polys)
        }

        return detection_result
