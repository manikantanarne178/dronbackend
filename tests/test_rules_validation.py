"""
Unit tests for Area Engine, Height Engine, Parking Engine, Rule Engine, Compliance Engine,
Green Building Engine, and Accessibility Engine.
"""

import unittest
from app.services.area_service import AreaService
from app.autodcr.height_engine import HeightEngine
from app.autodcr.parking_engine import ParkingEngine
from app.rules.rule_engine import RuleEngine
from app.autodcr.compliance_engine import ComplianceEngine
from app.autodcr.green_building_engine import GreenBuildingEngine
from app.autodcr.accessibility_engine import AccessibilityEngine
from app.services.setback_service import SetbackService


class TestRulesValidation(unittest.TestCase):

    def test_area_calculations(self):
        detection_results = {
            "plot": {"area": 1000.0},
            "buildings": [{"area": 400.0}],
            "parking": {"total_parking_area": 100.0},
            "floor_elements": {"total_landscape_area": 150.0, "total_open_space_area": 450.0, "total_balcony_area": 20.0}
        }
        
        areas = AreaService.calculate_all_areas(detection_results, floor_count=2)
        self.assertEqual(areas["plot_area"], 1000.0)
        self.assertEqual(areas["building_area"], 400.0)
        self.assertEqual(areas["ground_coverage_pct"], 40.0)
        self.assertEqual(areas["built_up_area"], 800.0)

    def test_height_engine(self):
        heights = HeightEngine.calculate_heights({}, floor_count=4)
        self.assertEqual(heights["number_of_floors"], 4)
        self.assertGreater(heights["building_height"], 10.0)

    def test_parking_engine(self):
        detected_parking = {"car_parking_count": 10, "bike_parking_count": 20, "accessible_parking_count": 1}
        res = ParkingEngine.calculate_parking_requirements(built_up_area=1000.0, occupancy_type="Residential", detected_parking=detected_parking)
        self.assertEqual(res["required_car_parking"], 10)
        self.assertTrue(res["is_parking_compliant"])

    def test_directional_setback_service(self):
        plot = {"points": [(0, 0), (20, 0), (20, 30), (0, 30)]}
        building = {"points": [(3, 5), (15, 5), (15, 20), (3, 20)]}
        road = {"direction": "north"}
        setbacks = SetbackService.calculate(plot, building, road)
        self.assertIn("front", setbacks)
        self.assertIn("rear", setbacks)
        self.assertIn("left", setbacks)
        self.assertIn("right", setbacks)
        self.assertGreater(setbacks["front"], 0.0)

    def test_green_building_engine(self):
        detection_results = {
            "amenities": {"total_solar_area": 50.0, "rwh_pit_count": 2, "stp_count": 1},
            "floor_elements": {"total_landscape_area": 200.0}
        }
        areas = {"plot_area": 1000.0, "building_area": 400.0}
        res = GreenBuildingEngine.evaluate(detection_results, areas, standard="GRIHA")
        self.assertEqual(res["standard_evaluated"], "GRIHA")
        self.assertGreaterEqual(res["overall_green_score"], 50.0)
        self.assertTrue(res["is_green_compliant"])

    def test_accessibility_engine(self):
        detection_results = {
            "parking": {"accessible_parking_count": 2},
            "circulation": {"lifts": [{"is_fire_lift": True}], "ramps": [{"ramp_type": "ACCESSIBLE", "slope_percentage": 6.0, "width": 1.5}]}
        }
        parsed_data = {}
        res = AccessibilityEngine.evaluate(detection_results, parsed_data)
        self.assertEqual(res["overall_accessibility_status"], "PASS")
        self.assertEqual(res["passed_checks"], 10)


if __name__ == "__main__":
    unittest.main()
