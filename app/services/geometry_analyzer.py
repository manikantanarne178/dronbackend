from math import sqrt


class GeometryAnalyzer:

    @staticmethod
    def to_2d(point):
        """
        Convert any point format to (x, y).

        Supports:
        - (x, y)
        - (x, y, z)
        - [x, y]
        - [x, y, z]
        - ezdxf.math.Vec2
        - ezdxf.math.Vec3
        - {"x": x, "y": y}
        """

        if isinstance(point, dict):
            return float(point["x"]), float(point["y"])

        if hasattr(point, "x") and hasattr(point, "y"):
            return float(point.x), float(point.y)

        return float(point[0]), float(point[1])

    @staticmethod
    def polygon_area(points):

        if isinstance(points, dict):
            points = points.get("points", [])

        if len(points) < 3:
            return 0

        if GeometryAnalyzer.to_2d(points[0]) == GeometryAnalyzer.to_2d(points[-1]):
            points = points[:-1]

        area = 0
        n = len(points)

        for i in range(n):
            x1, y1 = GeometryAnalyzer.to_2d(points[i])
            x2, y2 = GeometryAnalyzer.to_2d(points[(i + 1) % n])

            area += (x1 * y2) - (x2 * y1)

        return abs(area) / 2

    @staticmethod
    def polygon_perimeter(points):

        if isinstance(points, dict):
            points = points.get("points", [])

        if len(points) < 2:
            return 0

        if GeometryAnalyzer.to_2d(points[0]) == GeometryAnalyzer.to_2d(points[-1]):
            points = points[:-1]

        perimeter = 0
        n = len(points)

        for i in range(n):
            x1, y1 = GeometryAnalyzer.to_2d(points[i])
            x2, y2 = GeometryAnalyzer.to_2d(points[(i + 1) % n])

            perimeter += sqrt(
                (x2 - x1) ** 2 +
                (y2 - y1) ** 2
            )

        return perimeter

    @staticmethod
    def bounding_box(points):

        if isinstance(points, dict):
            points = points.get("points", [])

        if not points:
            return None

        if GeometryAnalyzer.to_2d(points[0]) == GeometryAnalyzer.to_2d(points[-1]):
            points = points[:-1]

        xs = []
        ys = []

        for p in points:
            x, y = GeometryAnalyzer.to_2d(p)
            xs.append(x)
            ys.append(y)

        return {
            "min_x": min(xs),
            "max_x": max(xs),
            "min_y": min(ys),
            "max_y": max(ys),
            "width": max(xs) - min(xs),
            "height": max(ys) - min(ys)
        }

    @staticmethod
    def centroid(points):

        if isinstance(points, dict):
            points = points.get("points", [])

        if not points:
            return [0, 0]

        if GeometryAnalyzer.to_2d(points[0]) == GeometryAnalyzer.to_2d(points[-1]):
            points = points[:-1]

        xs = []
        ys = []

        for p in points:
            x, y = GeometryAnalyzer.to_2d(p)
            xs.append(x)
            ys.append(y)

        return [
            sum(xs) / len(xs),
            sum(ys) / len(ys)
        ]

    @staticmethod
    def analyze_polygon(points):

        return {
            "area": GeometryAnalyzer.polygon_area(points),
            "perimeter": GeometryAnalyzer.polygon_perimeter(points),
            "bounding_box": GeometryAnalyzer.bounding_box(points),
            "centroid": GeometryAnalyzer.centroid(points)
        }