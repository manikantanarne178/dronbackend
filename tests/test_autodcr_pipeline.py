"""
Comprehensive Integration & End-to-End Tests for AutoDCR Subsystem.
Tests Real File Upload, Server UTC Timestamp Generation, Geometry Extraction,
Real Non-Zero Metric Calculations, Rule Validation, Scrutiny Report JSON,
and Professional Scrutiny PDF Generation.
"""

import io
import unittest
from datetime import datetime, timezone
import ezdxf
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


class TestAutoDCRPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def _create_sample_dxf_bytes(self) -> bytes:
        """Generates a valid real DXF file in memory with PLOT, BUILDING, ROAD, and PARKING layers."""
        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()

        # Plot boundary (40m x 30m = 1200 sqm)
        msp.add_lwpolyline(
            [(0, 0), (40, 0), (40, 30), (0, 30), (0, 0)],
            close=True,
            dxfattribs={"layer": "PLOT"}
        )

        # Building footprint (20m x 15m = 300 sqm)
        msp.add_lwpolyline(
            [(5, 5), (25, 5), (25, 20), (5, 20), (5, 5)],
            close=True,
            dxfattribs={"layer": "BUILDING"}
        )

        # Parking space
        msp.add_lwpolyline(
            [(28, 2), (33, 2), (33, 7), (28, 7), (28, 2)],
            close=True,
            dxfattribs={"layer": "PARKING"}
        )

        # Road text
        msp.add_text(
            "12.0M WIDE ROAD",
            dxfattribs={"layer": "ROAD", "insert": (20, -5), "height": 1.5}
        )

        buf = io.StringIO()
        doc.write(buf)
        return buf.getvalue().encode("utf-8")

    def _create_sample_png_bytes(self) -> bytes:
        """Generates a valid real PNG image in memory."""
        img = Image.new("RGB", (400, 300), color=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_01_cleanup_endpoint(self):
        """Verify cleanup removes old mock/dev data."""
        res = self.client.post("/api/autodcr/cleanup")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])

        # Project list should now be empty
        list_res = self.client.get("/api/autodcr/projects")
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(len(list_res.json()["projects"]), 0)

    def test_02_real_dxf_upload_and_metrics_calculation(self):
        """Upload a real DXF file and verify real non-zero plot area, built-up area, and FSI."""
        dxf_bytes = self._create_sample_dxf_bytes()
        files = {"file": ("residential_site_plan.dxf", dxf_bytes, "application/dxf")}
        data = {"zone": "Residential", "applicant_name": "Test Builder"}

        res = self.client.post("/api/autodcr/upload", files=files, data=data)
        self.assertEqual(res.status_code, 200)
        json_data = res.json()

        self.assertTrue(json_data["success"])
        self.assertIn("project_id", json_data)
        self.assertEqual(json_data["filename"], "residential_site_plan.dxf")
        self.assertEqual(json_data["file_type"], "DXF")
        self.assertIn("uploaded_at", json_data)

        # Verify uploaded_at is a real ISO datetime matching today's UTC year/month/day
        upload_dt = datetime.fromisoformat(json_data["uploaded_at"]).astimezone(timezone.utc)
        now_dt = datetime.now(timezone.utc)
        self.assertEqual(upload_dt.year, now_dt.year)
        self.assertEqual(upload_dt.month, now_dt.month)
        self.assertEqual(upload_dt.day, now_dt.day)

        # Check analysis metrics: Plot Area should be 1200 sqm, Building Area 300 sqm, FSI 0.25
        analysis = json_data.get("analysis", {})
        areas = analysis.get("areas", {})
        self.assertIsNotNone(areas.get("plot_area"))
        self.assertAlmostEqual(float(areas["plot_area"]), 1200.0, places=1)
        self.assertIsNotNone(areas.get("built_up_area"))
        self.assertAlmostEqual(float(areas["built_up_area"]), 300.0, places=1)
        self.assertIsNotNone(areas.get("fsi"))
        self.assertAlmostEqual(float(areas["fsi"]), 0.25, places=2)

    def test_03_get_projects_returns_real_database_records(self):
        """Verify GET /api/autodcr/projects returns the real database record."""
        res = self.client.get("/api/autodcr/projects")
        self.assertEqual(res.status_code, 200)
        projects = res.json()["projects"]
        self.assertGreaterEqual(len(projects), 1)

        proj = projects[0]
        self.assertEqual(proj["filename"], "residential_site_plan.dxf")
        self.assertEqual(proj["file_type"], "DXF")
        self.assertIsNotNone(proj["uploaded_at"])
        self.assertNotIn("2026-09-18T18:00:00Z", proj["uploaded_at"])

    def test_04_get_scrutiny_report_json(self):
        """Verify GET /api/autodcr/projects/{id}/scrutiny-report returns structured data matching actual file."""
        list_res = self.client.get("/api/autodcr/projects")
        project_id = list_res.json()["projects"][0]["project_id"]

        res = self.client.get(f"/api/autodcr/projects/{project_id}/scrutiny-report")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("project", data)
        self.assertIn("scrutiny", data)
        self.assertIn("analysis", data)
        self.assertIn("metrics", data)
        self.assertIn("rules", data)
        self.assertIn("summary", data)

        # Check metrics are real non-zero values
        metrics = data["metrics"]
        self.assertAlmostEqual(float(metrics["plot_area"]), 1200.0, places=1)
        self.assertAlmostEqual(float(metrics["built_up_area"]), 300.0, places=1)
        self.assertAlmostEqual(float(metrics["fsi"]), 0.25, places=2)
        self.assertAlmostEqual(float(metrics["ground_coverage_pct"]), 25.0, places=1)

    def test_05_download_scrutiny_report_pdf(self):
        """Verify GET /api/autodcr/projects/{id}/scrutiny-report/pdf generates a real professional PDF."""
        list_res = self.client.get("/api/autodcr/projects")
        project_id = list_res.json()["projects"][0]["project_id"]

        res = self.client.get(f"/api/autodcr/projects/{project_id}/scrutiny-report/pdf")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["content-type"], "application/pdf")
        self.assertIn(f"AutoDCR-{project_id}-Scrutiny-Report.pdf", res.headers["content-disposition"])

        # Check PDF header bytes
        pdf_bytes = res.content
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
        self.assertGreater(len(pdf_bytes), 2000)  # Real PDF is several kilobytes

    def test_06_image_upload_support(self):
        """Verify real PNG image upload and contour analysis."""
        png_bytes = self._create_sample_png_bytes()
        files = {"file": ("floor_layout.png", png_bytes, "image/png")}
        data = {"zone": "Residential"}

        res = self.client.post("/api/autodcr/upload", files=files, data=data)
        self.assertEqual(res.status_code, 200)
        json_data = res.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["file_type"], "PNG")
        self.assertIn("uploaded_at", json_data)

    def test_07_unsupported_format_handling(self):
        """Verify unsupported file formats return explicit error."""
        files = {"file": ("corrupted.xyz", b"invalid random bytes", "application/octet-stream")}
        res = self.client.post("/api/autodcr/upload", files=files)
        json_data = res.json()
        if res.status_code == 200:
            self.assertFalse(json_data["success"])
            self.assertIn("Unsupported", json_data["error"])

    def test_08_delete_project(self):
        """Verify DELETE /api/autodcr/projects/{id} deletes the project."""
        list_res = self.client.get("/api/autodcr/projects")
        projects = list_res.json()["projects"]
        target_id = projects[0]["project_id"]

        del_res = self.client.delete(f"/api/autodcr/projects/{target_id}")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])

        # Check that it's no longer in the list
        list_after = self.client.get("/api/autodcr/projects")
        ids_after = [p["project_id"] for p in list_after.json()["projects"]]
        self.assertNotIn(target_id, ids_after)


if __name__ == "__main__":
    unittest.main()
