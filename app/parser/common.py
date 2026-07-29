from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ParsedDrawing:

    layers: List[str] = field(default_factory=list)

    entities: List[Dict[str, Any]] = field(default_factory=list)

    texts: List[Dict[str, Any]] = field(default_factory=list)

    dimensions: List[Dict[str, Any]] = field(default_factory=list)

    blocks: List[Dict[str, Any]] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):

        return {
            "layers": self.layers,
            "entities": self.entities,
            "texts": self.texts,
            "dimensions": self.dimensions,
            "blocks": self.blocks,
            "metadata": self.metadata,
        }


class EntityFactory:

    @staticmethod
    def line(layer, start, end):
        return {
            "type": "LINE",
            "layer": layer,
            "start": list(start),
            "end": list(end)
        }

    @staticmethod
    def lwpolyline(layer, points, closed=False):
        return {
            "type": "LWPOLYLINE",
            "layer": layer,
            "points": [list(p) for p in points],
            "closed": closed
        }

    @staticmethod
    def polyline(layer, points, closed=False):
        return {
            "type": "POLYLINE",
            "layer": layer,
            "points": [list(p) for p in points],
            "closed": closed
        }

    @staticmethod
    def circle(layer, center, radius):
        return {
            "type": "CIRCLE",
            "layer": layer,
            "center": list(center),
            "radius": radius
        }

    @staticmethod
    def arc(layer, center, radius, start_angle, end_angle):
        return {
            "type": "ARC",
            "layer": layer,
            "center": list(center),
            "radius": radius,
            "start_angle": start_angle,
            "end_angle": end_angle
        }

    @staticmethod
    def text(layer, text, insert, height):
        return {
            "type": "TEXT",
            "layer": layer,
            "text": text,
            "insert": list(insert),
            "height": height
        }

    @staticmethod
    def mtext(layer, text, insert, height):
        return {
            "type": "MTEXT",
            "layer": layer,
            "text": text,
            "insert": list(insert),
            "height": height
        }

    @staticmethod
    def dimension(layer, start, end, value=None):
        return {
            "type": "DIMENSION",
            "layer": layer,
            "start": list(start),
            "end": list(end),
            "value": value
        }

    @staticmethod
    def block(layer, name, insert):
        return {
            "type": "BLOCK",
            "layer": layer,
            "name": name,
            "insert": list(insert)
        }

    @staticmethod
    def spline(layer, points):
        return {
            "type": "SPLINE",
            "layer": layer,
            "points": [list(p) for p in points]
        }

    @staticmethod
    def hatch(layer, boundary):
        return {
            "type": "HATCH",
            "layer": layer,
            "boundary": boundary
        }