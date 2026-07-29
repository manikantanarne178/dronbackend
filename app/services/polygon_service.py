class PolygonService:

    @staticmethod
    def extract_polygons(parsed_data):

        polygons = []

        for entity in parsed_data["entities"]:

            if entity["type"] == "LWPOLYLINE":

                if entity.get("closed"):

                    polygons.append(entity["points"])

        return polygons