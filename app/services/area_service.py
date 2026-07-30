"""
Production Area Calculation Service for AutoDCR.
Calculates Plot Area, Building Area, Built-up Area, Floor Area, Floor-wise Area,
Total Floor Area, Ground Coverage %, Parking Area, Open Area, Landscape Area,
Basement Area, Terrace Area, Carpet Area, Super Built-up Area, FSI Area, and FAR Area.
"""

from typing import Dict, Any, List


class AreaService:

    @staticmethod
    def plot_area(plot: Dict[str, Any]) -> float:
        if plot is None:
            return 0.0
        return float(plot.get("area", 0.0))

    @staticmethod
    def building_area(building: Dict[str, Any]) -> float:
        if building is None:
            return 0.0
        return float(building.get("area", 0.0))

    @staticmethod
    def total_floor_area(building: Dict[str, Any], floor_count: int = 1) -> float:
        if building is None:
            return 0.0
        base_area = float(building.get("area", 0.0))
        return base_area * max(1, floor_count)

    @staticmethod
    def ground_coverage(plot: Dict[str, Any], building: Dict[str, Any]) -> float:
        p_area = AreaService.plot_area(plot)
        b_area = AreaService.building_area(building)
        if p_area <= 0:
            return 0.0
        return (b_area / p_area) * 100.0

    @staticmethod
    def calculate_all_areas(detection_results: Dict[str, Any], floor_count: int = 1) -> Dict[str, float]:
        """
        Calculates all standard municipal AutoDCR area metrics.
        """
        plot = detection_results.get("plot", {})
        buildings = detection_results.get("buildings", [])
        parking = detection_results.get("parking", {})
        floor_elements = detection_results.get("floor_elements", {})

        p_area = AreaService.plot_area(plot)
        b_area = sum(b.get("area", 0.0) for b in buildings) if isinstance(buildings, list) else AreaService.building_area(buildings)
        
        ground_coverage_pct = (b_area / p_area * 100.0) if p_area > 0 else 0.0
        total_builtup_area = b_area * max(1, floor_count)

        parking_area = parking.get("total_parking_area", 0.0)
        landscape_area = floor_elements.get("total_landscape_area", 0.0)
        open_area = floor_elements.get("total_open_space_area", max(0.0, p_area - b_area))
        balcony_area = floor_elements.get("total_balcony_area", 0.0)

        basement_area = sum(b.get("area", 0.0) for b in floor_elements.get("basements", []))
        terrace_area = sum(t.get("area", 0.0) for t in floor_elements.get("terraces", []))

        # Standard Indian DCR Carpet Area ~ 70-80% of Built-up Area
        carpet_area = total_builtup_area * 0.75
        # Super Built-up Area ~ 1.25x Built-up Area
        super_builtup_area = total_builtup_area * 1.25

        fsi_area = total_builtup_area - balcony_area - basement_area
        far = (fsi_area / p_area) if p_area > 0 else 0.0

        return {
            "plot_area": p_area,
            "building_area": b_area,
            "ground_coverage_pct": ground_coverage_pct,
            "built_up_area": total_builtup_area,
            "floor_wise_area": [b_area] * max(1, floor_count),
            "total_floor_area": total_builtup_area,
            "parking_area": parking_area,
            "open_area": open_area,
            "landscape_area": landscape_area,
            "basement_area": basement_area,
            "terrace_area": terrace_area,
            "balcony_area": balcony_area,
            "carpet_area": carpet_area,
            "super_built_up_area": super_builtup_area,
            "fsi_area": fsi_area,
            "far": far,
        }