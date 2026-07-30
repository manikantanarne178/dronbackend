"""
AutoDCR Geometry Engine package.
Re-exports GeometryEngine, UnitConverter, DistanceCalculator, and PolygonOps.
"""

from app.geometry.engine import GeometryEngine
from app.geometry.unit_converter import UnitConverter
from app.geometry.distance import DistanceCalculator
from app.geometry.polygon_ops import PolygonOps

__all__ = [
    "GeometryEngine",
    "UnitConverter",
    "DistanceCalculator",
    "PolygonOps",
]
