import math


class RoadDetectionService:

    @staticmethod
    def detect(plot):
        """
        Detect probable road-facing edge.

        Strategy:
        1. Take plot polygon.
        2. Find the longest edge.
        3. Assume it is road-facing.
        4. Determine orientation.
        """

        if plot is None:
            return None

        points = plot.get("points", [])

        if len(points) < 4:
            return None

        longest = None
        max_length = 0

        for i in range(len(points) - 1):

            p1 = points[i]
            p2 = points[i + 1]

            length = math.hypot(
                p2[0] - p1[0],
                p2[1] - p1[1]
            )

            if length > max_length:
                max_length = length
                longest = (p1, p2)

        if longest is None:
            return None

        p1, p2 = longest

        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]

        if abs(dx) >= abs(dy):
            direction = "east" if dx > 0 else "west"
        else:
            direction = "north" if dy > 0 else "south"

        return {
            "side": "front",
            "direction": direction,
            "width": None,          # Calculated after ROAD entity detection
            "edge": [p1, p2],
            "edge_length": round(max_length, 3)
        }