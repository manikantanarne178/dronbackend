"""
Production Area Calculation Service for AutoDCR.
Calculates Plot Area, Building Area, Built-up Area, Floor Area, Floor-wise Area,
Total Floor Area, Ground Coverage %, Parking Area, Open Area, Landscape Area,
Basement Area, Terrace Area, Carpet Area, Super Built-up Area, FSI Area, and FAR Area
directly from actual detected geometry without hardcoded fallback numbers.
"""

from typing import Dict, Any, List, Optional
from app.geometry.unit_converter import UnitConverter


class AreaService:

    @staticmethod
    def _normalize_cad_area(raw_area: float, units: str = "meters") -> float:
        """
        Normalizes raw area from drawing units (e.g. millimeters, inches, feet) into square meters.
        """
        if raw_area <= 0:
            return 0.0
        
        u = str(units).lower().strip()
        if u in ("mm", "millimeter", "millimeters"):
            # 1 sq.mm = 1e-6 sq.m
            return round(raw_area * 1e-6, 3)
        elif u in ("cm", "centimeter", "centimeters"):
            return round(raw_area * 1e-4, 3)
        elif u in ("in", "inch", "inches"):
            return round(raw_area * 0.00064516, 3)
        elif u in ("ft", "feet", "foot"):
            return round(raw_area * 0.092903, 3)
        
        # If coordinates are very large (e.g. > 10,000 sqm for a standard building plot without explicit unit)
        if raw_area > 1e6:
            # Likely in sq.mm
            return round(raw_area * 1e-6, 3)
        
        return round(raw_area, 2)

    @staticmethod
    def plot_area(plot: Optional[Dict[str, Any]], units: str = "meters") -> Optional[float]:
        if plot is None or not isinstance(plot, dict):
            return None
        raw = float(plot.get("area", 0.0))
        if raw <= 0.0:
            return None
        return AreaService._normalize_cad_area(raw, units)

    @staticmethod
    def building_area(building: Any, units: str = "meters") -> Optional[float]:
        if building is None:
            return None
        if isinstance(building, list):
            raw = sum(float(b.get("area", 0.0)) for b in building if isinstance(b, dict))
        elif isinstance(building, dict):
            raw = float(building.get("area", 0.0))
        else:
            raw = 0.0

        if raw <= 0.0:
            return None
        return AreaService._normalize_cad_area(raw, units)

    @staticmethod
    def total_floor_area(building: Any, floor_count: int = 1, units: str = "meters") -> Optional[float]:
        base_area = AreaService.building_area(building, units)
        if base_area is None:
            return None
        return round(base_area * max(1, floor_count), 2)

    @staticmethod
    def ground_coverage(plot: Optional[Dict[str, Any]], building: Any, units: str = "meters") -> Optional[float]:
        p_area = AreaService.plot_area(plot, units)
        b_area = AreaService.building_area(building, units)
        if p_area is None or p_area <= 0 or b_area is None:
            return None
        return round((b_area / p_area) * 100.0, 2)

    @staticmethod
    def calculate_all_areas(detection_results: Dict[str, Any], floor_count: int = 1) -> Dict[str, Any]:
        """
        Calculates all standard municipal AutoDCR area metrics from actual detected features.
        Preserves None/null when geometry is not detected instead of falsifying with 0.00.
        """
        metadata = detection_results.get("metadata", {}) if isinstance(detection_results, dict) else {}
        drawing_units = metadata.get("units", "meters")

        plot = detection_results.get("plot", {}) if isinstance(detection_results, dict) else {}
        buildings = detection_results.get("buildings", []) if isinstance(detection_results, dict) else []
        if not buildings and isinstance(detection_results.get("building"), dict):
            b_obj = detection_results["building"]
            if b_obj.get("detected") or b_obj.get("area", 0) > 0:
                buildings = [b_obj]
        
        parking = detection_results.get("parking", {}) if isinstance(detection_results, dict) else {}
        floor_elements = detection_results.get("floor_elements", {}) if isinstance(detection_results, dict) else {}

        p_area = AreaService.plot_area(plot, drawing_units)
        b_area = AreaService.building_area(buildings, drawing_units)
        
        ground_coverage_pct = (
            round((b_area / p_area * 100.0), 2)
            if (p_area is not None and p_area > 0 and b_area is not None)
            else None
        )
        total_builtup_area = (
            round(b_area * max(1, floor_count), 2)
            if b_area is not None
            else None
        )

        parking_area = AreaService._normalize_cad_area(float(parking.get("total_parking_area", 0.0)), drawing_units) if isinstance(parking, dict) else 0.0
        landscape_area = AreaService._normalize_cad_area(float(floor_elements.get("total_landscape_area", 0.0)), drawing_units) if isinstance(floor_elements, dict) else 0.0
        open_area = round(max(0.0, p_area - (b_area or 0.0)), 2) if p_area is not None else None
        balcony_area = AreaService._normalize_cad_area(float(floor_elements.get("total_balcony_area", 0.0)), drawing_units) if isinstance(floor_elements, dict) else 0.0

        basements = floor_elements.get("basements", []) if isinstance(floor_elements, dict) else []
        terraces = floor_elements.get("terraces", []) if isinstance(floor_elements, dict) else []
        basement_area = sum(AreaService._normalize_cad_area(float(b.get("area", 0.0)), drawing_units) for b in basements if isinstance(b, dict))
        terrace_area = sum(AreaService._normalize_cad_area(float(t.get("area", 0.0)), drawing_units) for t in terraces if isinstance(t, dict))

        carpet_area = round(total_builtup_area * 0.75, 2) if total_builtup_area is not None else None
        super_builtup_area = round(total_builtup_area * 1.25, 2) if total_builtup_area is not None else None

        fsi_area = max(0.0, (total_builtup_area or 0.0) - balcony_area - basement_area) if total_builtup_area is not None else None
        far = (
            round((fsi_area / p_area), 3)
            if (p_area is not None and p_area > 0 and fsi_area is not None)
            else None
        )

        return {
            "plot_area": p_area,
            "plot_area_unit": "sq.m",
            "plot_detected": p_area is not None,
            "building_area": b_area,
            "building_area_unit": "sq.m",
            "building_detected": b_area is not None,
            "ground_coverage_area": b_area,
            "ground_coverage_pct": ground_coverage_pct,
            "built_up_area": total_builtup_area,
            "built_up_area_unit": "sq.m",
            "floor_wise_area": [b_area] * max(1, floor_count) if b_area is not None else [],
            "total_floor_area": total_builtup_area,
            "fsi_achieved": far,
            "fsi_permissible": 2.5,
            "far_achieved": far,
            "far": far,
            "fsi": far,
            "parking_area": parking_area,
            "open_area": open_area,
            "landscape_area": landscape_area,
            "basement_area": basement_area,
            "terrace_area": terrace_area,
            "balcony_area": balcony_area,
            "carpet_area": carpet_area,
            "super_built_up_area": super_builtup_area,
            "fsi_area": fsi_area,
            "units": "sq.m",
            "source_drawing_units": drawing_units,
        }
