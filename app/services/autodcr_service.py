import os
import uuid
from pathlib import Path
from fastapi import UploadFile

from app.parser.dxf_parser import DXFParser
from app.services.geometry_service import GeometryService
from app.services.plot_detector import PlotDetector
from app.services.building_detector import BuildingDetector
from app.services.road_detection import RoadDetectionService
from app.services.setback_service import SetbackService
from app.services.area_service import AreaService
from app.services.rule_config_service import RuleConfigService
from sqlalchemy.orm import Session


class AutoDCRService:
    """Service that orchestrates the AutoDCR workflow.

    It handles file storage, parsing, geometry extraction, metric calculations,
    rule validation and report generation.
    """

    UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads" / "autodcr"

    def __init__(self, db: Session):
        """Create the service.

        Args:
            db: SQLAlchemy session used by ``RuleConfigService`` to fetch zone
                specific parameters.
        """
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        self.rule_config = RuleConfigService(db)

    async def save_uploaded_file(self, file: UploadFile) -> str:
        """Persist an uploaded CAD file and return the absolute path.

        The function generates a UUID based filename to avoid collisions.
        """
        file_id = str(uuid.uuid4())
        extension = Path(file.filename).suffix
        dest_path = self.UPLOAD_DIR / f"{file_id}{extension}"
        with dest_path.open("wb") as buffer:
            content = await file.read()
            buffer.write(content)
        return str(dest_path)

    async def parse_file(self, file_path: str) -> dict:
        """Parse a DXF file using the existing ``DXFParser``.

        Args:
            file_path: Absolute path to the uploaded file.

        Returns:
            Dict representation of the drawing produced by ``DXFParser``.
        """
        # ``DXFParser.parse`` expects a filesystem path.
        drawing_dict = DXFParser.parse(file_path)
        return drawing_dict

    def _extract_geometry(self, parsed: dict) -> dict:
        """Organise parsed entities and detect plot / building boundaries.

        Returns a dictionary with the following keys (where available):
            plot_boundary, building_boundary, road, setbacks, plotArea,
            buildingArea, totalFloorArea, groundCoverage, roadWidth.
        """
        # Organise raw entities by semantic groups.
        geometry = GeometryService.organize(parsed)

        # Detect plot – using polygons classified as plot based on layer naming.
        plot = PlotDetector.detect(geometry.get("polygons", []))

        # Detect building within the plot.
        building = BuildingDetector.detect(geometry.get("polygons", []), plot)

        # Detect road information.
        road = RoadDetectionService.detect(plot) if plot else None

        # Calculate setbacks.
        setbacks = SetbackService.calculate(plot, building, road)

        # Metric calculations.
        plot_area = AreaService.plot_area(plot) if plot else 0.0
        building_area = AreaService.building_area(building) if building else 0.0
        # For simplicity, assume floors are stored under building["floors"] as a list.
        floors = building.get("floors", []) if building else []
        floor_multiplier = max(len(floors), 1)
        total_floor_area = building_area * floor_multiplier
        ground_coverage = (
            AreaService.ground_coverage(plot, building) if plot and building else 0.0
        )
        road_width = road.get("width") if road else 0.0

        return {
            "plot_boundary": plot,
            "building_boundary": building,
            "road": road,
            "roadWidth": road_width,
            "setbacks": setbacks,
            "plotArea": plot_area,
            "buildingArea": building_area,
            "totalFloorArea": total_floor_area,
            "groundCoverage": ground_coverage,
        }

    def _calculate_metrics(self, geom: dict) -> dict:
        """Derive regulatory metrics from geometry data.

        Returns a dict containing FSI, FAR, coverage, parking, etc.
        """
        plot_area = geom.get("plotArea", 0.0)
        building_area = geom.get("buildingArea", 0.0)
        total_floor = geom.get("totalFloorArea", 0.0)
        coverage = geom.get("groundCoverage", 0.0)
        # Simple parking estimation – count parking entities if present.
        parking_entities = geom.get("parking", [])
        parking_area = len(parking_entities) * 2.5  # assume 2.5 sqm per spot

        fsi = total_floor / plot_area if plot_area else 0.0
        far = building_area / plot_area if plot_area else 0.0

        return {
            "FSI": round(fsi, 3),
            "FAR": round(far, 3),
            "coverage": round(coverage, 2),
            "parkingArea": round(parking_area, 2),
            "roadWidth": geom.get("roadWidth", 0.0),
            "setbacks": geom.get("setbacks", {}),
            "plotArea": round(plot_area, 2),
            "buildingArea": round(building_area, 2),
        }

    async def validate(self, file_path: str, zone: str) -> dict:
        """Validate a drawing against zone‑specific regulations.

        The function parses the file, extracts geometry, calculates metrics and
        compares them to values obtained from ``RuleConfigService``.
        """
        parsed = await self.parse_file(file_path)
        geom = self._extract_geometry(parsed)
        metrics = self._calculate_metrics(geom)

        results = []
        # Plot Area rule – assuming rule config stores a maximum allowed area.
        expected_plot = self.rule_config.get_value("Plot Area", "max")
        if metrics["plotArea"] <= expected_plot:
            results.append({"rule": "Plot Area", "expected": f"≤ {expected_plot} sqm", "actual": f"{metrics['plotArea']} sqm", "status": "PASS"})
        else:
            results.append({"rule": "Plot Area", "expected": f"≤ {expected_plot} sqm", "actual": f"{metrics['plotArea']} sqm", "status": "FAIL", "suggestion": "Reduce plot area or re‑evaluate layout."})

        # Front Setback rule.
        expected_front = self.rule_config.get_value("Front Setback", "min")
        front_setback = metrics["setbacks"].get("front", 0.0)
        if front_setback >= expected_front:
            results.append({"rule": "Front Setback", "expected": f"≥ {expected_front} m", "actual": f"{front_setback} m", "status": "PASS"})
        else:
            results.append({"rule": "Front Setback", "expected": f"≥ {expected_front} m", "actual": f"{front_setback} m", "status": "FAIL", "suggestion": f"Increase front setback by {round(expected_front - front_setback, 2)} m."})

        # FSI rule.
        expected_fsi = self.rule_config.get_value("FSI", "max")
        if metrics["FSI"] <= expected_fsi:
            results.append({"rule": "FSI", "expected": f"≤ {expected_fsi}", "actual": f"{metrics['FSI']}", "status": "PASS"})
        else:
            results.append({"rule": "FSI", "expected": f"≤ {expected_fsi}", "actual": f"{metrics['FSI']}", "status": "FAIL", "suggestion": "Reduce floor count or floor area."})

        # Parking area rule.
        expected_parking = self.rule_config.get_value("Parking Area", "min")
        if metrics["parkingArea"] >= expected_parking:
            results.append({"rule": "Parking Area", "expected": f"≥ {expected_parking} sqm", "actual": f"{metrics['parkingArea']} sqm", "status": "PASS"})
        else:
            results.append({"rule": "Parking Area", "expected": f"≥ {expected_parking} sqm", "actual": f"{metrics['parkingArea']} sqm", "status": "FAIL", "suggestion": f"Add {round(expected_parking - metrics['parkingArea'], 2)} sqm of parking."})

        return {
            "file_id": Path(file_path).name,
            "zone": zone,
            "metrics": metrics,
            "results": results,
        }

    async def generate_report(self, file_path: str, zone: str, format: str = "json") -> dict:
        """Generate a compliance report based on validation results.
        """
        validation = await self.validate(file_path, zone)
        pass_count = sum(1 for r in validation["results"] if r["status"] == "PASS")
        fail_count = len(validation["results"]) - pass_count
        overall = round((pass_count / max(len(validation["results"]), 1)) * 100, 2)
        report = {
            "file_id": validation["file_id"],
            "zone": zone,
            "format": format,
            "summary": {
                "passCount": pass_count,
                "failCount": fail_count,
                "overallCompliance": overall,
            },
            "metrics": validation["metrics"],
            "details": validation["results"],
        }
        return report

    async def get_result(self, result_id: str) -> dict:
        """Placeholder for fetching a persisted result.
        """
        return {"result_id": result_id, "status": "placeholder"}
