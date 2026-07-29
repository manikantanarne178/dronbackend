import ifcopenshell

from app.parser.common import ParsedDrawing, EntityFactory


class IFCParser:

    @staticmethod
    def parse(file_path: str):

        model = ifcopenshell.open(file_path)

        drawing = ParsedDrawing()

        drawing.layers.extend([
            "IFC_WALLS",
            "IFC_SLABS",
            "IFC_COLUMNS",
            "IFC_DOORS",
            "IFC_WINDOWS",
            "IFC_SPACES",
            "IFC_BEAMS",
        ])

        IFCParser._parse_walls(model, drawing)
        IFCParser._parse_slabs(model, drawing)
        IFCParser._parse_columns(model, drawing)
        IFCParser._parse_beams(model, drawing)
        IFCParser._parse_doors(model, drawing)
        IFCParser._parse_windows(model, drawing)
        IFCParser._parse_spaces(model, drawing)

        drawing.metadata = {
            "source_format": "IFC",
            "entity_count": len(drawing.entities),
            "layer_count": len(drawing.layers),
            "text_count": len(drawing.texts),
            "block_count": len(drawing.blocks),
            "dimension_count": len(drawing.dimensions),
        }

        return drawing.to_dict()

    @staticmethod
    def _location(product):

        try:

            p = (
                product.ObjectPlacement
                .RelativePlacement
                .Location
                .Coordinates
            )

            if len(p) == 2:
                return (p[0], p[1])

            return (p[0], p[1])

        except Exception:
            return (0.0, 0.0)

    @staticmethod
    def _name(product):

        return product.Name if product.Name else product.GlobalId

    @staticmethod
    def _append(layer, product, drawing):

        x, y = IFCParser._location(product)

        entity = {
            "type": product.is_a(),
            "layer": layer,
            "name": IFCParser._name(product),
            "location": [x, y],
        }

        drawing.entities.append(entity)

    @staticmethod
    def _parse_walls(model, drawing):

        for wall in model.by_type("IfcWall"):
            IFCParser._append("IFC_WALLS", wall, drawing)

    @staticmethod
    def _parse_slabs(model, drawing):

        for slab in model.by_type("IfcSlab"):
            IFCParser._append("IFC_SLABS", slab, drawing)

    @staticmethod
    def _parse_columns(model, drawing):

        for column in model.by_type("IfcColumn"):
            IFCParser._append("IFC_COLUMNS", column, drawing)

    @staticmethod
    def _parse_beams(model, drawing):

        for beam in model.by_type("IfcBeam"):
            IFCParser._append("IFC_BEAMS", beam, drawing)

    @staticmethod
    def _parse_doors(model, drawing):

        for door in model.by_type("IfcDoor"):
            IFCParser._append("IFC_DOORS", door, drawing)

    @staticmethod
    def _parse_windows(model, drawing):

        for window in model.by_type("IfcWindow"):
            IFCParser._append("IFC_WINDOWS", window, drawing)

    @staticmethod
    def _parse_spaces(model, drawing):

        for space in model.by_type("IfcSpace"):
            IFCParser._append("IFC_SPACES", space, drawing)