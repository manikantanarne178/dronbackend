from math import sqrt


class DistanceService:

    @staticmethod
    def point_distance(p1, p2):

        return sqrt(
            (p1[0] - p2[0]) ** 2 +
            (p1[1] - p2[1]) ** 2
        )

    @staticmethod
    def point_to_segment_distance(point, start, end):

        px, py = point
        x1, y1 = start
        x2, y2 = end

        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            return DistanceService.point_distance(point, start)

        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))

        nearest = (
            x1 + t * dx,
            y1 + t * dy
        )

        return DistanceService.point_distance(point, nearest)

    @staticmethod
    def minimum_distance(poly1, poly2):

        if not poly1 or not poly2:
            return 0.0

        minimum = float("inf")

        if poly1[0] == poly1[-1]:
            poly1 = poly1[:-1]

        if poly2[0] == poly2[-1]:
            poly2 = poly2[:-1]

        for point in poly1:

            for i in range(len(poly2)):

                start = poly2[i]
                end = poly2[(i + 1) % len(poly2)]

                d = DistanceService.point_to_segment_distance(
                    point,
                    start,
                    end
                )

                minimum = min(minimum, d)

        for point in poly2:

            for i in range(len(poly1)):

                start = poly1[i]
                end = poly1[(i + 1) % len(poly1)]

                d = DistanceService.point_to_segment_distance(
                    point,
                    start,
                    end
                )

                minimum = min(minimum, d)

        return round(minimum, 3)