"""
Unit tests for AutoDCR Automatic Detection Engine, Parking, Vertical Circulation, Floor, and Amenities Detectors.
"""

import unittest
from app.autodcr.parking_detector import ParkingDetector
from app.autodcr.vertical_circ_detector import VerticalCirculationDetector
from app.autodcr.floor_detector import FloorDetector
from app.autodcr.amenities_detector import AmenitiesDetector
from app.autodcr.detector_engine import AutomaticDetectionEngine


class TestDetection(unittest.TestCase):

    def test_parking_detector(self):
        parsed_sample = {
            "entities": {
                "polylines": [
                    {"layer": "PARKING_CAR_SLOT", "points": [(0, 0), (2.5, 0), (2.5, 5), (0, 5), (0, 0)]},
                    {"layer": "BIKE_PARK", "points": [(10, 0), (11, 0), (11, 2), (10, 2), (10, 0)]},
                ]
            },
            "metadata": {}
        }
        
        parking_res = ParkingDetector.detect_parking(parsed_sample)
        self.assertGreaterEqual(parking_res["car_parking_count"], 1)
        self.assertGreaterEqual(parking_res["bike_parking_count"], 1)

    def test_circulation_detector(self):
        parsed_sample = {
            "entities": {
                "polylines": [
                    {"layer": "LIFT_SHAFT", "points": [(0, 0), (2, 0), (2, 2), (0, 2)]},
                    {"layer": "FIRE_STAIRCASE", "points": [(5, 0), (8, 0), (8, 4), (5, 4)]},
                ]
            }
        }
        
        circ_res = VerticalCirculationDetector.detect_circulation(parsed_sample)
        self.assertEqual(circ_res["lift_count"], 1)
        self.assertEqual(circ_res["fire_staircase_count"], 1)

    def test_automatic_detection_engine_master(self):
        parsed_sample = {
            "entities": {
                "polylines": [
                    {"layer": "PLOT_BOUNDARY", "points": [(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)]},
                    {"layer": "BUILDING_LINE", "points": [(20, 20), (60, 20), (60, 60), (20, 60), (20, 20)]},
                ]
            },
            "metadata": {}
        }
        
        res = AutomaticDetectionEngine.detect_all(parsed_sample)
        self.assertIn("plot", res)
        self.assertIn("buildings", res)
        self.assertIn("parking", res)
        self.assertIn("circulation", res)


if __name__ == "__main__":
    unittest.main()
