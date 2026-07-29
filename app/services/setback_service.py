from app.services.distance_service import DistanceService


class SetbackService:

    @staticmethod
    def calculate(plot, building, road=None):

        if plot is None or building is None:
            return {
                "front": 0.0,
                "rear": 0.0,
                "left": 0.0,
                "right": 0.0
            }

        distance = DistanceService.minimum_distance(
            plot["points"],
            building["points"]
        )

        # TODO:
        # Replace with actual directional setback calculation.
        # For now, use the minimum distance on all sides.

        return {
            "front": round(distance, 3),
            "rear": round(distance, 3),
            "left": round(distance, 3),
            "right": round(distance, 3)
        }