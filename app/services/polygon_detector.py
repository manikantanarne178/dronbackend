from math import sqrt


class PolygonDetector:

    TOLERANCE = 0.001

    @staticmethod
    def to_2d(point):
        """
        Convert point to (x, y).
        Supports:
        (x, y)
        (x, y, z)
        [x, y]
        [x, y, z]
        """
        return point[0], point[1]

    @staticmethod
    def distance(p1, p2):
        x1, y1 = PolygonDetector.to_2d(p1)
        x2, y2 = PolygonDetector.to_2d(p2)

        return sqrt(
            (x1 - x2) ** 2 +
            (y1 - y2) ** 2
        )

    @staticmethod
    def points_equal(p1, p2):
        return (
            PolygonDetector.distance(p1, p2)
            <= PolygonDetector.TOLERANCE
        )

    @staticmethod
    def polygon_area(points):

        if len(points) < 4:
            return 0

        area = 0

        for i in range(len(points) - 1):

            x1, y1 = PolygonDetector.to_2d(points[i])
            x2, y2 = PolygonDetector.to_2d(points[i + 1])

            area += (x1 * y2) - (x2 * y1)

        return abs(area) / 2

    @staticmethod
    def centroid(points):

        if len(points) <= 1:
            return [0, 0]

        xs = []
        ys = []

        for p in points[:-1]:
            x, y = PolygonDetector.to_2d(p)
            xs.append(x)
            ys.append(y)

        return [
            sum(xs) / len(xs),
            sum(ys) / len(ys)
        ]

    @staticmethod
    def get_lines(entities):

        lines = []

        for entity in entities:

            entity_type = entity["type"]

            if entity_type == "LINE":

                lines.append({
                    "start": entity["start"],
                    "end": entity["end"],
                    "used": False
                })

            elif entity_type in ["LWPOLYLINE", "POLYLINE"]:

                pts = entity["points"]

                for i in range(len(pts) - 1):
                    lines.append({
                        "start": pts[i],
                        "end": pts[i + 1],
                        "used": False
                    })

                if entity.get("closed", False):
                    lines.append({
                        "start": pts[-1],
                        "end": pts[0],
                        "used": False
                    })

        return lines

    @staticmethod
    def detect(entities):

        polygons = []

        # Closed polylines
        for entity in entities:

            if entity["type"] in ["LWPOLYLINE", "POLYLINE"]:

                if entity.get("closed", False):

                    pts = entity["points"][:]

                    if not PolygonDetector.points_equal(
                        pts[0],
                        pts[-1]
                    ):
                        pts.append(pts[0])

                    polygons.append({
                        "points": pts,
                        "closed": True,
                        "area": PolygonDetector.polygon_area(pts),
                        "centroid": PolygonDetector.centroid(pts)
                    })

        if polygons:
            polygons.sort(
                key=lambda x: x["area"],
                reverse=True
            )
            return polygons

        # Build polygons from LINE entities
        lines = PolygonDetector.get_lines(entities)

        for line in lines:

            if line["used"]:
                continue

            polygon = [
                line["start"],
                line["end"]
            ]

            line["used"] = True

            searching = True

            while searching:

                searching = False

                last = polygon[-1]

                for candidate in lines:

                    if candidate["used"]:
                        continue

                    if PolygonDetector.points_equal(
                        last,
                        candidate["start"]
                    ):

                        polygon.append(candidate["end"])
                        candidate["used"] = True
                        searching = True
                        break

                    elif PolygonDetector.points_equal(
                        last,
                        candidate["end"]
                    ):

                        polygon.append(candidate["start"])
                        candidate["used"] = True
                        searching = True
                        break

            if len(polygon) >= 4:

                if PolygonDetector.points_equal(
                    polygon[0],
                    polygon[-1]
                ):

                    polygons.append({
                        "points": polygon,
                        "closed": True,
                        "area": PolygonDetector.polygon_area(polygon),
                        "centroid": PolygonDetector.centroid(polygon)
                    })

        polygons.sort(
            key=lambda x: x["area"],
            reverse=True
        )

        return polygons