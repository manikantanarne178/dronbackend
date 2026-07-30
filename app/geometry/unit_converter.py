"""
Unit Converter module for AutoDCR Geometry Engine.
Provides static helper methods for unit conversions (mm, cm, m, ft, in, etc.)
and DXF header variable mapping ($INSUNITS).
"""

from typing import List, Tuple, Dict, Any, Union


class UnitConverter:
    """
    Utility class for handling unit conversions in AutoDCR.
    """

    # Mapping of unit names to scale factor relative to meters
    TO_METERS: Dict[str, float] = {
        "mm": 0.001,
        "millimeter": 0.001,
        "millimeters": 0.001,
        "cm": 0.01,
        "centimeter": 0.01,
        "centimeters": 0.01,
        "m": 1.0,
        "meter": 1.0,
        "meters": 1.0,
        "km": 1000.0,
        "kilometer": 1000.0,
        "in": 0.0254,
        "inch": 0.0254,
        "inches": 0.0254,
        "ft": 0.3048,
        "feet": 0.3048,
        "foot": 0.3048,
        "yd": 0.9144,
        "yard": 0.9144,
        "yards": 0.9144,
    }

    # DXF header $INSUNITS enum mapping
    DXF_INSUNITS: Dict[int, str] = {
        0: "unitless",
        1: "in",
        2: "ft",
        3: "mi",
        4: "mm",
        5: "cm",
        6: "m",
        7: "km",
        8: "microinches",
        9: "mils",
        10: "yd",
        11: "angstroms",
        12: "nanometers",
        13: "microns",
        14: "decimeters",
        15: "decameters",
        16: "hectometers",
        17: "gigameters",
        18: "AU",
        19: "lightyears",
        20: "parsecs",
    }

    @classmethod
    def get_unit_from_dxf_code(cls, code: int) -> str:
        """Returns standard unit string from DXF $INSUNITS integer code."""
        return cls.DXF_INSUNITS.get(code, "m")

    @classmethod
    def get_conversion_factor(cls, from_unit: str, to_unit: str) -> float:
        """Calculates multiplication scale factor to convert length from from_unit to to_unit."""
        from_u = str(from_unit).lower().strip()
        to_u = str(to_unit).lower().strip()

        from_m = cls.TO_METERS.get(from_u, 1.0)
        to_m = cls.TO_METERS.get(to_u, 1.0)

        if to_m == 0:
            return 1.0

        return from_m / to_m

    @classmethod
    def convert_length(cls, val: float, from_unit: str, to_unit: str) -> float:
        """Converts a scalar length value."""
        return val * cls.get_conversion_factor(from_unit, to_unit)

    @classmethod
    def convert_area(cls, val: float, from_unit: str, to_unit: str) -> float:
        """Converts a scalar area value (uses square of length conversion factor)."""
        factor = cls.get_conversion_factor(from_unit, to_unit)
        return val * (factor ** 2)

    @classmethod
    def convert_coordinates(
        cls, coords: List[Tuple[float, ...]], from_unit: str, to_unit: str
    ) -> List[Tuple[float, ...]]:
        """Converts a list of (x, y) or (x, y, z) coordinate tuples."""
        factor = cls.get_conversion_factor(from_unit, to_unit)
        if factor == 1.0:
            return coords

        converted = []
        for pt in coords:
            converted.append(tuple(c * factor for c in pt))
        return converted
