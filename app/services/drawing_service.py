import os
import uuid
import shutil
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.parser.parser_service import ParserService
from app.services.geometry_service import GeometryService
from app.services.geometry_analyzer import GeometryAnalyzer
from app.services.building_detector import BuildingDetector
from app.services.polygon_detector import PolygonDetector
from app.services.plot_detector import PlotDetector
from app.rules.rule_engine import RuleEngine
from app.models.drawing import Drawing

UPLOAD_DIR = "app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class DrawingService:

    @staticmethod
    def save_drawing(file, db: Session):
        drawing_id = str(uuid.uuid4())
        _, extension = os.path.splitext(file.filename)
        clean_ext = extension.replace(".", "").lower()

        filename = f"{drawing_id}.{clean_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        now = datetime.now(timezone.utc)

        # Persist Drawing record in DB
        drawing_record = Drawing(
            id=drawing_id,
            filename=file.filename,
            file_type=clean_ext.upper(),
            file_path=file_path,
            uploaded_at=now,
        )
        db.add(drawing_record)
        db.commit()

        # Parse drawing
        parsed_data = ParserService.parse(file_path)

        # Organize geometry
        geometry = GeometryService.organize(parsed_data)

        # Detect polygons
        polygons = PolygonDetector.detect(parsed_data.get("entities", []))

        # Analyze polygons
        analysis = [
            GeometryAnalyzer.analyze_polygon(polygon)
            for polygon in polygons
        ]

        # Detect plot
        plot = PlotDetector.detect(polygons)

        # Detect building
        building = BuildingDetector.detect(polygons, plot)

        # Validate rules
        rule_results = RuleEngine.validate_comprehensive(
            areas={"plot_area": plot.get("area", 0.0) if plot else 0.0, "built_up_area": sum(b.get("area", 0.0) for b in building) if isinstance(building, list) else (building.get("area", 0.0) if building else 0.0)},
            heights={"building_height": 10.0, "number_of_floors": 1},
            parking={"car_parking_count": 1, "is_parking_compliant": True},
            detection_results={"plot": plot, "building": building}
        )

        return {
            "drawing_id": drawing_id,
            "filename": file.filename,
            "file_path": file_path,
            "file_type": clean_ext.upper(),
            "uploaded_at": now.isoformat(),
            "status": "Uploaded Successfully",
            "parsed_data": parsed_data,
            "geometry": geometry,
            "polygon_analysis": analysis,
            "plot": plot,
            "building": building,
            "rules": rule_results,
        }