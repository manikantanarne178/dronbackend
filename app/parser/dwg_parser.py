import os

from app.parser.converter import DWGConverter
from app.parser.dxf_parser import DXFParser


class DWGParser:
    """
    DWG Parser

    Workflow:
        DWG
          ↓
    ODA File Converter
          ↓
        DXF
          ↓
     DXFParser
    """

    @staticmethod
    def parse(file_path: str):

        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)

        extension = os.path.splitext(file_path)[1].lower()

        if extension != ".dwg":
            raise ValueError("Input file must be a DWG.")

        converter = DWGConverter()

        if not converter.available():
            raise RuntimeError(
                "ODA File Converter is not installed or configured."
            )

        dxf_path = converter.convert(file_path)

        result = DXFParser.parse(dxf_path)

        result.setdefault("metadata", {})

        result["metadata"].update({
            "source_format": "DWG",
            "converted_to": "DXF",
            "converted_file": dxf_path
        })

        return result