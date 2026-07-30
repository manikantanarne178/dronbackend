"""
IFC Drawing Parser module.
Parses IFC BIM models, extracts geometric entities, spatial hierarchy (Storey, Building, Site),
and properties into common ParsedDrawing format.
"""

import ifcopenshell
from typing import Dict, Any
from app.parser.common import ParsedDrawing, EntityFactory


class IFCParser:

    @staticmethod
    def parse(file_path: str) -> Dict[str, Any]:
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
            "IFC_STAIRS",
            "IFC_ROOFS",
            "IFC_RAILINGS",
        ])

        IFCParser._parse_walls(model, drawing)
        IFCParser._parse_slabs(model, drawing)
        IFCParser._parse_columns(model, drawing)
        IFCParser._parse_beams(model, drawing)
        IFCParser._parse_doors(model, drawing)
        IFCParser._parse_windows(model, drawing)
        IFCParser._parse_spaces(model, drawing)
        IFCParser._parse_stairs(model, drawing)
        IFCParser._parse_roofs(model, drawing)

        building_labels = [b.Name for b in model.by_type("IfcBuilding") if getattr(b, "Name", None)]
        floor_labels = [s.Name for s in model.by_type("IfcBuildingStorey") if getattr(s, "Name", None)]
        room_labels = [sp.LongName or sp.Name for sp in model.by_type("IfcSpace") if getattr(sp, "Name", None) or getattr(sp, "LongName", None)]

        drawing.metadata = {
            "source_format": "IFC",
            "units": "m",
            "drawing_scale": 1.0,
            "north_direction": 90.0,
            "entity_count": len(drawing.entities),
            "layer_count": len(drawing.layers),
            "text_count": len(drawing.texts),
            "block_count": len(drawing.blocks),
            "dimension_count": len(drawing.dimensions),
            "building_labels": building_labels,
            "floor_labels": floor_labels,
            "room_labels": room_labels,
            "road_labels": [],
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
            return (float(p[0]), float(p[1]))
        except Exception:
            return (0.0, 0.0)

    @staticmethod
    def _name(product):
        return product.Name if getattr(product, "Name", None) else product.GlobalId

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

    @staticmethod
    def _parse_stairs(model, drawing):
        for stair in model.by_type("IfcStairFlight"):
            IFCParser._append("IFC_STAIRS", stair, drawing)

    @staticmethod
    def _parse_roofs(model, drawing):
        for roof in model.by_type("IfcRoof"):
            IFCParser._append("IFC_ROOFS", roof, drawing)