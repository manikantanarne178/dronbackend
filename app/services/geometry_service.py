class GeometryService:

    @staticmethod
    def organize(parsed_data):

        geometry = {
            "plot_boundary": [],
            "building_boundary": [],
            "roads": [],
            "parking": [],
            "stairs": [],
            "lifts": [],
            "texts": [],
            "dimensions": [],
            "polygons": [],
            "others": []
        }

        for entity in parsed_data["entities"]:

            layer = entity.get("layer", "").lower()
            entity_type = entity.get("type", "").upper()

            # ----------------------------
            # Layer Classification
            # ----------------------------

            if "plot" in layer:
                geometry["plot_boundary"].append(entity)

            elif "building" in layer:
                geometry["building_boundary"].append(entity)

            elif "road" in layer:
                geometry["roads"].append(entity)

            elif "parking" in layer:
                geometry["parking"].append(entity)

            elif "stair" in layer:
                geometry["stairs"].append(entity)

            elif "lift" in layer:
                geometry["lifts"].append(entity)

            # ----------------------------
            # Entity Classification
            # ----------------------------

            elif entity_type in ("TEXT", "MTEXT"):
                geometry["texts"].append(entity)

            elif entity_type == "DIMENSION":
                geometry["dimensions"].append(entity)

            elif entity_type in ("LINE", "LWPOLYLINE", "POLYLINE"):
                geometry["polygons"].append(entity)

            else:
                geometry["others"].append(entity)

        return geometry