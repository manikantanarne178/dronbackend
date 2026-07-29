import os
import uuid
import shutil

from sqlalchemy.orm import Session

from app.parser.parser_service import ParserService
from app.services.geometry_service import GeometryService
from app.services.geometry_analyzer import GeometryAnalyzer
from app.services.building_detector import BuildingDetector
from app.services.polygon_detector import PolygonDetector
from app.services.plot_detector import PlotDetector
from app.rules.rule_engine import RuleEngine

UPLOAD_DIR = "app/uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


class DrawingService:

    @staticmethod
    def save_drawing(file, db: Session):

        # Generate drawing ID
        drawing_id = str(uuid.uuid4())

        # File extension
        _, extension = os.path.splitext(file.filename)
        extension = extension.replace(".", "").lower()

        filename = f"{drawing_id}.{extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Parse drawing
        parsed_data = ParserService.parse(file_path)

        # Organize geometry
        geometry = GeometryService.organize(parsed_data)

        # Detect polygons
        polygons = PolygonDetector.detect(parsed_data["entities"])

        # Analyze polygons
        analysis = [
            GeometryAnalyzer.analyze_polygon(polygon)
            for polygon in polygons
        ]

        # Detect plot
        plot = PlotDetector.detect(polygons)

        # Detect building
        building = BuildingDetector.detect(
            polygons,
            plot
        )

        # Validate rules
        rule_results = RuleEngine.validate(
            plot,
            building,
            db
        )

        return {
            "drawing_id": drawing_id,
            "filename": filename,
            "file_path": file_path,
            "file_type": extension.upper(),
            "uploaded_at": None,
            "status": "Uploaded Successfully",
            "parsed_data": parsed_data,
            "geometry": geometry,
            "polygon_analysis": analysis,
            "plot": plot,
            "building": building,
            "rules": rule_results,
        }