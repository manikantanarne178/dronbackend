from app.services.road_detection import RoadDetectionService
from app.services.setback_service import SetbackService


class SetbackRule:

    @staticmethod
    def check(plot, building, config):

        if plot is None:
            return {
                "rule": "Setback",
                "status": "FAIL",
                "reason": "Plot not detected"
            }

        if building is None:
            return {
                "rule": "Setback",
                "status": "FAIL",
                "reason": "Building not detected"
            }

        road = RoadDetectionService.detect(plot)

        setbacks = SetbackService.calculate(
            plot,
            building,
            road
        )

        required = float(
            config.get_value(
                "setback",
                "min_front"
            )
        )

        details = {}
        overall = "PASS"

        for side, distance in setbacks.items():

            status = "PASS" if distance >= required else "FAIL"

            if status == "FAIL":
                overall = "FAIL"

            details[side] = {
                "required": required,
                "actual": round(distance, 2),
                "status": status
            }

        return {
            "rule": "Setback",
            "status": overall,
            "details": details
        }