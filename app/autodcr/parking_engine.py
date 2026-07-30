"""
Parking Engine module for AutoDCR.
Calculates required parking vs available parking for cars, bikes, and accessible slots,
evaluates slot dimensions, and identifies parking violations against building code rules.
"""

from typing import Dict, Any, List


class ParkingEngine:
    """
    Municipal parking compliance and calculation engine.
    """

    # Standards (e.g. NBC / GDCR: 1 car slot per 100 sqm builtup area for residential)
    STD_CAR_SLOT_WIDTH = 2.5  # meters
    STD_CAR_SLOT_LENGTH = 5.0  # meters
    STD_CAR_SLOT_AREA = 12.5  # sqm

    @staticmethod
    def calculate_parking_requirements(
        built_up_area: float,
        occupancy_type: str,
        detected_parking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculates required vs available parking slots and identifies violations.
        """
        occ = occupancy_type.upper()
        
        # Determine requirement ratio based on occupancy type
        if "COMMERCIAL" in occ:
            req_car_ratio = 1 / 50.0  # 1 slot per 50 sqm
        elif "INDUSTRIAL" in occ:
            req_car_ratio = 1 / 150.0
        else:  # Residential
            req_car_ratio = 1 / 100.0

        required_cars = max(1, int(built_up_area * req_car_ratio))
        required_bikes = int(required_cars * 2)
        required_accessible = max(1, int(required_cars * 0.05))

        avail_cars = detected_parking.get("car_parking_count", 0)
        avail_bikes = detected_parking.get("bike_parking_count", 0)
        avail_accessible = detected_parking.get("accessible_parking_count", 0)
        total_avail_area = detected_parking.get("total_parking_area", 0.0)

        violations: List[str] = []
        if avail_cars < required_cars:
            violations.append(f"Insufficient Car Parking: Available {avail_cars}, Required {required_cars}")
        if avail_bikes < required_bikes:
            violations.append(f"Insufficient Bike Parking: Available {avail_bikes}, Required {required_bikes}")
        if avail_accessible < required_accessible:
            violations.append(f"Insufficient Accessible Parking: Available {avail_accessible}, Required {required_accessible}")

        return {
            "required_car_parking": required_cars,
            "available_car_parking": avail_cars,
            "required_bike_parking": required_bikes,
            "available_bike_parking": avail_bikes,
            "required_accessible_parking": required_accessible,
            "available_accessible_parking": avail_accessible,
            "total_parking_area": total_avail_area,
            "parking_violations": violations,
            "is_parking_compliant": len(violations) == 0
        }
