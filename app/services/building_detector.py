class BuildingDetector:

    @staticmethod
    def normalize_point(point):
        """
        Converts different point formats into (x, y).

        Supported:
        (x, y)
        (x, y, z)
        [x, y]
        [x, y, z]
        {"x": ..., "y": ...}
        """

        if isinstance(point, dict):
            return float(point["x"]), float(point["y"])

        if isinstance(point, (list, tuple)):
            if len(point) >= 2:
                return float(point[0]), float(point[1])

        raise ValueError(f"Invalid point format: {point}")

    @staticmethod
    def point_in_polygon(point, polygon):

        x, y = BuildingDetector.normalize_point(point)

        polygon = [
            BuildingDetector.normalize_point(p)
            for p in polygon
        ]

        inside = False
        j = len(polygon) - 1

        for i in range(len(polygon)):

            xi, yi = polygon[i]
            xj, yj = polygon[j]

            if (yi > y) != (yj > y):

                intersect = (
                    x <
                    ((xj - xi) * (y - yi)) /
                    ((yj - yi) if (yj - yi) != 0 else 1e-9)
                    + xi
                )

                if intersect:
                    inside = not inside

            j = i

        return inside

    @staticmethod
    def detect(polygons, plot):

        if plot is None:
            return None

        plot_points = [
            BuildingDetector.normalize_point(p)
            for p in plot["points"]
        ]

        plot_area = plot["area"]

        candidates = []

        for polygon in polygons:

            if polygon["area"] >= plot_area:
                continue

            inside = True

            polygon_points = [
                BuildingDetector.normalize_point(p)
                for p in polygon["points"]
            ]

            # Ignore duplicated closing point if present
            if len(polygon_points) > 1 and polygon_points[0] == polygon_points[-1]:
                check_points = polygon_points[:-1]
            else:
                check_points = polygon_points

            for point in check_points:

                if not BuildingDetector.point_in_polygon(
                    point,
                    plot_points
                ):
                    inside = False
                    break

            if inside:
                candidates.append({
                    "points": polygon_points,
                    "area": polygon["area"],
                    "centroid": polygon["centroid"]
                })

        if not candidates:
            return None

        candidates.sort(
            key=lambda x: x["area"],
            reverse=True
        )

        building = candidates[0]

        return {
            "points": building["points"],
            "area": building["area"],
            "centroid": building["centroid"]
        }