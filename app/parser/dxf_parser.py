import ezdxf

from app.parser.common import ParsedDrawing, EntityFactory


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

                    block = EntityFactory.block(
                        layer,
                        entity.dxf.name,
                        entity.dxf.insert
                    )

                    drawing.blocks.append(block)
                    drawing.entities.append(block)

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

                    drawing.entities.append(
                        EntityFactory.hatch(
                            layer,
                            boundaries
                        )
                    )

            except Exception as e:

                print(
                    f"Skipped {entity_type}: {e}"
                )

        drawing.metadata = {

            "entity_count": len(drawing.entities),

            "layer_count": len(drawing.layers),

            "text_count": len(drawing.texts),

            "block_count": len(drawing.blocks),

            "dimension_count": len(drawing.dimensions)
        }

        return drawing.to_dict()