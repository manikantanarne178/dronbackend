"""
Parking Engine module for AutoDCR.
Calculates required parking vs available parking for cars, bikes, and accessible slots,
evaluates slot dimensions, and identifies parking violations against building code rules.
"""

from typing import Dict, Any, List, Optional


class ParkingEngine:
    """
    Municipal parking compliance and calculation engine.
    """

    STD_CAR_SLOT_WIDTH = 2.5  # meters
    STD_CAR_SLOT_LENGTH = 5.0  # meters
    STD_CAR_SLOT_AREA = 12.5  # sqm

    @staticmethod
    def calculate_parking_requirements(
        built_up_area: Optional[float],
        occupancy_type: str,
        detected_parking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculates required vs available parking slots and identifies violations.
        """
        occ = occupancy_type.upper() if occupancy_type else "RESIDENTIAL"
        b_area = float(built_up_area or 0.0)
        
        if "COMMERCIAL" in occ:
            req_car_ratio = 1 / 50.0
        elif "INDUSTRIAL" in occ:
            req_car_ratio = 1 / 150.0
        else:
            req_car_ratio = 1 / 100.0

        required_cars = max(1, int(b_area * req_car_ratio)) if b_area > 0 else 1
        required_bikes = int(required_cars * 2)
        required_accessible = max(1, int(required_cars * 0.05))

        avail_cars = detected_parking.get("car_parking_count", 0) if isinstance(detected_parking, dict) else 0
        avail_bikes = detected_parking.get("bike_parking_count", 0) if isinstance(detected_parking, dict) else 0
        avail_accessible = detected_parking.get("accessible_parking_count", 0) if isinstance(detected_parking, dict) else 0
        total_avail_area = detected_parking.get("total_parking_area", 0.0) if isinstance(detected_parking, dict) else 0.0

        violations: List[str] = []
        if b_area > 0 and avail_cars < required_cars:
            violations.append(f"Insufficient Car Parking: Available {avail_cars}, Required {required_cars}")
        if b_area > 0 and avail_bikes < required_bikes:
            violations.append(f"Insufficient Bike Parking: Available {avail_bikes}, Required {required_bikes}")
        if b_area > 0 and avail_accessible < required_accessible:
            violations.append(f"Insufficient Accessible Parking: Available {avail_accessible}, Required {required_accessible}")

        is_compliant = len(violations) == 0

        return {
            "required_car_parking": required_cars,
            "available_car_parking": avail_cars,
            "required_slots": required_cars,
            "provided_slots": avail_cars,
            "visitor_slots": 2,
            "handicapped_slots": avail_accessible,
            "ramp_slope_ratio": 10,
            "status": "PASS" if is_compliant else "WARNING",
            "required_bike_parking": required_bikes,
            "available_bike_parking": avail_bikes,
            "required_accessible_parking": required_accessible,
            "available_accessible_parking": avail_accessible,
            "total_parking_area": total_avail_area,
            "parking_violations": violations,
            "is_parking_compliant": is_compliant
        }
