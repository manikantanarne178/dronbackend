from app.parser.dxf_parser import DXFParser
from app.parser.dwg_parser import DWGParser
from app.parser.ifc_parser import IFCParser
from app.parser.pdf_parser import PDFParser


class ParserService:

    @staticmethod
    def parse(file_path: str):

        extension = file_path.lower().split(".")[-1]

        if extension == "dxf":
            return DXFParser.parse(file_path)

        if extension == "dwg":
            return DWGParser.parse(file_path)

        if extension == "ifc":
            return IFCParser.parse(file_path)

        if extension == "pdf":
            return PDFParser.parse(file_path)

        raise ValueError(f"Unsupported file type: {extension}")