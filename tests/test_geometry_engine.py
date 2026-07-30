"""
Unit tests for AutoDCR Geometry Engine, Unit Converter, Distance Calculator, and Polygon Ops.
"""

import unittest
from shapely.geometry import Polygon
from app.geometry.engine import GeometryEngine
from app.geometry.unit_converter import UnitConverter
from app.geometry.distance import DistanceCalculator
from app.geometry.polygon_ops import PolygonOps


class TestGeometryEngine(unittest.TestCase):

    def test_geometry_engine_basic(self):
        pts = [(0, 0), (10, 0), (10, 10), (0, 10)]
        poly = GeometryEngine.to_shapely_polygon(pts)
        
        self.assertEqual(GeometryEngine.polygon_area(poly), 100.0)
        self.assertEqual(GeometryEngine.polygon_perimeter(poly), 40.0)
        self.assertEqual(GeometryEngine.polygon_centroid(poly), (5.0, 5.0))
        
        bbox = GeometryEngine.bounding_box(poly)
        self.assertEqual(bbox["width"], 10.0)
        self.assertEqual(bbox["height"], 10.0)

    def test_unit_converter(self):
        factor = UnitConverter.get_conversion_factor("mm", "m")
        self.assertEqual(factor, 0.001)
        
        converted_len = UnitConverter.convert_length(1000, "mm", "m")
        self.assertEqual(converted_len, 1.0)
        
        converted_area = UnitConverter.convert_area(1, "m", "mm")
        self.assertEqual(converted_area, 1000000.0)

    def test_distance_calculator(self):
        dist_pt = DistanceCalculator.point_to_point((0, 0), (3, 4))
        self.assertEqual(dist_pt, 5.0)
        
        poly1 = GeometryEngine.to_shapely_polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
        poly2 = GeometryEngine.to_shapely_polygon([(5, 0), (7, 0), (7, 2), (5, 2)])
        
        clearance = DistanceCalculator.polygon_to_polygon(poly1, poly2)
        self.assertEqual(clearance, 3.0)

    def test_polygon_ops_closed_detection(self):
        lines = [
            {"points": [(0, 0), (10, 0)]},
            {"points": [(10, 0), (10, 10)]},
            {"points": [(10, 10), (0, 10)]},
            {"points": [(0, 10), (0, 0)]},
        ]
        polys = PolygonOps.detect_closed_polygons(lines)
        self.assertEqual(len(polys), 1)
        self.assertEqual(polys[0].area, 100.0)


if __name__ == "__main__":
    unittest.main()
