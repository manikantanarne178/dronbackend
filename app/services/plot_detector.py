class PlotDetector:

    @staticmethod
    def detect(polygons):

        if not polygons:
            return None

        polygons = sorted(
            polygons,
            key=lambda x: x["area"],
            reverse=True
        )

        plot = polygons[0]

        return {
            "points": plot["points"],
            "area": plot["area"],
            "centroid": plot["centroid"]
        }