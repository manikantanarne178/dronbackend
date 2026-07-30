import re

import ezdxf

from app.parser.common import ParsedDrawing, EntityFactory


# ---------------------------------------------------------------------------
# DXF unit codes ($INSUNITS) → human-readable name
# ---------------------------------------------------------------------------
_DXF_UNIT_MAP = {
    0: "unitless",
    1: "inches",
    2: "feet",
    3: "miles",
    4: "millimeters",
    5: "centimeters",
    6: "meters",
    7: "kilometers",
    8: "microinches",
    9: "mils",
    10: "yards",
    11: "angstroms",
    12: "nanometers",
    13: "microns",
    14: "decimeters",
    15: "decameters",
    16: "hectometers",
    17: "gigameters",
    18: "astronomical_units",
    19: "light_years",
    20: "parsecs",
}

# ---------------------------------------------------------------------------
# Patterns used to classify TEXT / MTEXT into semantic labels
# ---------------------------------------------------------------------------
_BUILDING_LABEL_RE = re.compile(
    r"\b(building|bldg|structure|tower|wing|block)\b", re.IGNORECASE
)
_ROOM_LABEL_RE = re.compile(
    r"\b(room|hall|kitchen|bedroom|bathroom|toilet|wc|living|dining|"
    r"office|lobby|corridor|passage|store|utility)\b",
    re.IGNORECASE,
)
_ROAD_LABEL_RE = re.compile(
    r"\b(road|street|lane|path|highway|avenue|drive|d\.p\.|d\.p)\b",
    re.IGNORECASE,
)
_FLOOR_LABEL_RE = re.compile(
    r"\b(floor|storey|story|ground\s*floor|first\s*floor|basement|"
    r"terrace|stilt|podium|mezzanine|gf|ff|sf|tf)\b",
    re.IGNORECASE,
)


class DXFParser:

    @staticmethod
    def parse(file_path: str):

        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()

        drawing = ParsedDrawing()

        for entity in msp:

            layer = entity.dxf.layer

            if layer not in drawing.layers:
                drawing.layers.append(layer)

            entity_type = entity.dxftype()

            try:

                if entity_type == "LINE":

                    drawing.entities.append(
                        EntityFactory.line(
                            layer,
                            entity.dxf.start,
                            entity.dxf.end
                        )
                    )

                elif entity_type == "LWPOLYLINE":

                    drawing.entities.append(
                        EntityFactory.lwpolyline(
                            layer,
                            [(p[0], p[1]) for p in entity.get_points()],
                            entity.closed
                        )
                    )

                elif entity_type == "POLYLINE":

                    points = []

                    for v in entity.vertices:
                        points.append((v.dxf.location.x, v.dxf.location.y))

                    drawing.entities.append(
                        EntityFactory.polyline(
                            layer,
                            points,
                            entity.is_closed
                        )
                    )

                elif entity_type == "CIRCLE":

                    drawing.entities.append(
                        EntityFactory.circle(
                            layer,
                            entity.dxf.center,
                            entity.dxf.radius
                        )
                    )

                elif entity_type == "ARC":

                    drawing.entities.append(
                        EntityFactory.arc(
                            layer,
                            entity.dxf.center,
                            entity.dxf.radius,
                            entity.dxf.start_angle,
                            entity.dxf.end_angle
                        )
                    )

                elif entity_type == "TEXT":

                    text = EntityFactory.text(
                        layer,
                        entity.dxf.text,
                        entity.dxf.insert,
                        entity.dxf.height
                    )

                    drawing.texts.append(text)
                    drawing.entities.append(text)

                elif entity_type == "MTEXT":

                    text = EntityFactory.mtext(
                        layer,
                        entity.text,
                        entity.dxf.insert,
                        entity.dxf.char_height
                    )

                    drawing.texts.append(text)
                    drawing.entities.append(text)

                elif entity_type == "INSERT":

                    # ---------------------------------------------------
                    # Existing block record (kept for backward compat)
                    # ---------------------------------------------------
                    block = EntityFactory.block(
                        layer,
                        entity.dxf.name,
                        entity.dxf.insert
                    )

                    drawing.blocks.append(block)
                    drawing.entities.append(block)

                    # ---------------------------------------------------
                    # Enhanced INSERT with attributes
                    # ---------------------------------------------------
                    attrib_list = []
                    if hasattr(entity, "attribs"):
                        for attrib in entity.attribs:
                            attrib_dict = {
                                "tag": attrib.dxf.tag,
                                "text": attrib.dxf.text,
                                "layer": attrib.dxf.layer,
                                "insert": list(attrib.dxf.insert),
                            }
                            attrib_list.append(attrib_dict)
                            drawing.attributes.append(attrib_dict)

                    insert_ent = EntityFactory.insert_entity(
                        layer,
                        entity.dxf.name,
                        entity.dxf.insert,
                        attributes=attrib_list,
                        rotation=getattr(entity.dxf, "rotation", 0.0),
                        x_scale=getattr(entity.dxf, "xscale", 1.0),
                        y_scale=getattr(entity.dxf, "yscale", 1.0),
                    )
                    drawing.inserts.append(insert_ent)

                elif entity_type == "DIMENSION":

                    definition = entity.dxf.defpoint
                    target = entity.dxf.defpoint2

                    dim = EntityFactory.dimension(
                        layer,
                        definition,
                        target
                    )

                    drawing.dimensions.append(dim)
                    drawing.entities.append(dim)

                elif entity_type == "SPLINE":

                    control_points = []

                    for p in entity.control_points:
                        control_points.append((p.x, p.y))

                    drawing.entities.append(
                        EntityFactory.spline(
                            layer,
                            control_points
                        )
                    )

                elif entity_type == "HATCH":

                    boundaries = []

                    for path in entity.paths:

                        try:

                            pts = []

                            for edge in path.edges:

                                if hasattr(edge, "start"):
                                    pts.append(
                                        (
                                            edge.start[0],
                                            edge.start[1]
                                        )
                                    )

                            boundaries.append(pts)

                        except Exception:
                            pass

                    hatch_ent = EntityFactory.hatch(
                        layer,
                        boundaries
                    )
                    drawing.entities.append(hatch_ent)
                    drawing.hatches.append(hatch_ent)

                # ---------------------------------------------------
                # NEW: ELLIPSE support
                # ---------------------------------------------------
                elif entity_type == "ELLIPSE":

                    drawing.entities.append(
                        EntityFactory.ellipse(
                            layer,
                            entity.dxf.center,
                            entity.dxf.major_axis,
                            entity.dxf.ratio,
                            entity.dxf.start_param,
                            entity.dxf.end_param,
                        )
                    )

                # ---------------------------------------------------
                # NEW: LEADER support
                # ---------------------------------------------------
                elif entity_type == "LEADER":

                    vertices = []
                    if hasattr(entity, "vertices"):
                        vertices = [
                            (v.x, v.y) if hasattr(v, "x") else (v[0], v[1])
                            for v in entity.vertices
                        ]

                    annotation_text = None
                    if hasattr(entity.dxf, "annotation_type"):
                        annotation_text = str(entity.dxf.annotation_type)

                    leader_ent = EntityFactory.leader(
                        layer, vertices, annotation_text
                    )
                    drawing.entities.append(leader_ent)
                    drawing.leaders.append(leader_ent)

            except Exception as e:

                print(
                    f"Skipped {entity_type}: {e}"
                )

        # ---------------------------------------------------------------
        # Extract header variables for units, scale, north direction
        # ---------------------------------------------------------------
        header = doc.header
        units_code = header.get("$INSUNITS", 0)
        units_name = _DXF_UNIT_MAP.get(units_code, "unknown")
        drawing_scale = header.get("$DIMSCALE", 1.0)

        north_direction = 0.0
        try:
            north_vec = header.get("$NORTHDIRECTION", None)
            if north_vec is not None:
                north_direction = float(north_vec)
        except Exception:
            pass

        # ---------------------------------------------------------------
        # Classify text entities into semantic labels
        # ---------------------------------------------------------------
        building_labels = []
        room_labels = []
        road_labels = []
        floor_labels = []

        for txt in drawing.texts:
            content = txt.get("text", "")
            insert_pt = txt.get("insert", [0, 0])

            label_entry = {"text": content, "insert": insert_pt}

            if _BUILDING_LABEL_RE.search(content):
                building_labels.append(label_entry)
            if _ROOM_LABEL_RE.search(content):
                room_labels.append(label_entry)
            if _ROAD_LABEL_RE.search(content):
                road_labels.append(label_entry)
            if _FLOOR_LABEL_RE.search(content):
                floor_labels.append(label_entry)

        # ---------------------------------------------------------------
        # Build metadata
        # ---------------------------------------------------------------
        drawing.metadata = {

            "source_format": "DXF",

            "entity_count": len(drawing.entities),

            "layer_count": len(drawing.layers),

            "text_count": len(drawing.texts),

            "block_count": len(drawing.blocks),

            "dimension_count": len(drawing.dimensions),

            "insert_count": len(drawing.inserts),

            "attribute_count": len(drawing.attributes),

            "hatch_count": len(drawing.hatches),

            "leader_count": len(drawing.leaders),

            "units": units_name,

            "units_code": units_code,

            "drawing_scale": drawing_scale,

            "north_direction": north_direction,

            "labels": {
                "building": building_labels,
                "room": room_labels,
                "road": road_labels,
                "floor": floor_labels,
            },
        }

        return drawing.to_dict()