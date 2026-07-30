"""
Height Engine module for AutoDCR.
Calculates Building Height, Floor Height, Plinth Height, Parapet Height,
Terrace Height, Basement Depth, and Number of Floors based on CAD elevations/sections or metadata.
"""

from typing import Dict, Any


class HeightEngine:
    """
    Production height calculation engine for AutoDCR.
    """

    DEFAULT_FLOOR_HEIGHT = 3.0  # meters
    DEFAULT_PLINTH_HEIGHT = 0.6  # meters
    DEFAULT_PARAPET_HEIGHT = 1.2  # meters
    DEFAULT_BASEMENT_DEPTH = 3.3  # meters

    @staticmethod
    def calculate_heights(parsed_data: Dict[str, Any], floor_count: int = 1) -> Dict[str, float]:
        """
        Calculates all building height metrics.
        """
        metadata = parsed_data.get("metadata", {})
        
        # Look for height values in metadata or calculate estimates
        plinth_height = float(metadata.get("plinth_height", HeightEngine.DEFAULT_PLINTH_HEIGHT))
        floor_height = float(metadata.get("floor_height", HeightEngine.DEFAULT_FLOOR_HEIGHT))
        parapet_height = float(metadata.get("parapet_height", HeightEngine.DEFAULT_PARAPET_HEIGHT))
        basement_depth = float(metadata.get("basement_depth", HeightEngine.DEFAULT_BASEMENT_DEPTH))

        num_floors = max(1, int(metadata.get("floor_count", floor_count)))
        
        building_height = plinth_height + (num_floors * floor_height) + parapet_height
        terrace_height = plinth_height + (num_floors * floor_height)

        return {
            "building_height": building_height,
            "floor_height": floor_height,
            "plinth_height": plinth_height,
            "parapet_height": parapet_height,
            "terrace_height": terrace_height,
            "basement_depth": basement_depth,
            "number_of_floors": num_floors,
        }
