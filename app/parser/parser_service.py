import os
from app.parser.dxf_parser import DXFParser
from app.parser.dwg_parser import DWGParser
from app.parser.ifc_parser import IFCParser
from app.parser.pdf_parser import PDFParser
from app.parser.image_parser import ImageDrawingParser


class ParserService:
    """
    Unified Multi-Format CAD/BIM/Raster Drawing Parsing Service.
    Supports DXF, DWG, IFC, PDF, PNG, JPG, JPEG, BMP, TIFF.
    """

    IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "tiff", "tif", "webp"}

    @staticmethod
    def parse(file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File does not exist: {file_path}")

        extension = file_path.lower().split(".")[-1]

        if extension == "dxf":
            return DXFParser.parse(file_path)

        if extension == "dwg":
            return DWGParser.parse(file_path)

        if extension == "ifc":
            return IFCParser.parse(file_path)

        if extension == "pdf":
            return PDFParser.parse(file_path)

        if extension in ParserService.IMAGE_EXTENSIONS:
            return ImageDrawingParser.parse(file_path)

        raise ValueError(f"Unsupported file format: .{extension}. Supported: DXF, DWG, PDF, IFC, PNG, JPG, BMP")