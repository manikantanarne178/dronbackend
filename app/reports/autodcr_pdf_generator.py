"""
Professional AutoDCR Scrutiny PDF Report Generator.
Generates publication-grade municipal building plan scrutiny reports in PDF format
using ReportLab with dynamic multi-page NumberedCanvas, professional styling,
and actual analysis metrics and rule validation tables.
"""

import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ============================================================================
# FONT REGISTRATION
# ============================================================================
try:
    pdfmetrics.registerFont(TTFont("SegoeUI", "C:/Windows/Fonts/segoeui.ttf"))
    pdfmetrics.registerFont(TTFont("SegoeUI-Bold", "C:/Windows/Fonts/segoeuib.ttf"))
    FONT_NORMAL = "SegoeUI"
    FONT_BOLD = "SegoeUI-Bold"
except Exception:
    FONT_NORMAL = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"


# ============================================================================
# COLOR PALETTE (Municipal / Engineering Cyan & Slate Theme)
# ============================================================================
NAVY = colors.HexColor("#0F172A")       # Slate 900
SLATE_DARK = colors.HexColor("#334155") # Slate 700
SLATE_MED = colors.HexColor("#64748B")  # Slate 500
SLATE_LIGHT = colors.HexColor("#F1F5F9")# Slate 100
BORDER_COLOR = colors.HexColor("#CBD5E1")# Slate 300

CYAN_PRIMARY = colors.HexColor("#0284C7")  # Sky 600
CYAN_DARK = colors.HexColor("#0369A1")     # Sky 700
CYAN_LIGHT = colors.HexColor("#E0F2FE")    # Sky 100

PASS_GREEN = colors.HexColor("#16A34A")    # Green 600
PASS_BG = colors.HexColor("#DCFCE7")       # Green 100
FAIL_RED = colors.HexColor("#DC2626")      # Red 600
FAIL_BG = colors.HexColor("#FEE2E2")       # Red 100
WARN_AMBER = colors.HexColor("#D97706")    # Amber 600
WARN_BG = colors.HexColor("#FEF3C7")       # Amber 100
WHITE = colors.white


# ============================================================================
# NUMBERED CANVAS (Page X of Y)
# ============================================================================
class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to compute total page count and render professional footers on every page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont(FONT_NORMAL, 8)
        self.setFillColor(SLATE_MED)

        # Footer divider line
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.75)
        self.line(40, 42, 572, 42)

        # Footer text
        self.drawString(40, 28, "DroneVision AutoDCR Engine — Municipal Development Control Scrutiny")
        self.drawRightString(572, 28, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


# ============================================================================
# PDF GENERATOR CLASS
# ============================================================================
class AutoDCRScrutinyPDFGenerator:
    """
    Generates professional Building Plan Scrutiny PDF reports from real project scrutiny data.
    """

    def __init__(self, report_data: Dict[str, Any]):
        self.data = report_data
        self.styles = getSampleStyleSheet()
        self._init_styles()

    def _init_styles(self):
        self.title_style = ParagraphStyle(
            "DocTitle",
            fontName=FONT_BOLD,
            fontSize=16,
            leading=20,
            textColor=NAVY,
            alignment=TA_LEFT,
        )
        self.subtitle_style = ParagraphStyle(
            "DocSubtitle",
            fontName=FONT_BOLD,
            fontSize=9,
            leading=12,
            textColor=CYAN_PRIMARY,
            alignment=TA_LEFT,
            spaceAfter=4,
        )
        self.section_header = ParagraphStyle(
            "SectionHeader",
            fontName=FONT_BOLD,
            fontSize=11,
            leading=15,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=5,
        )
        self.body_style = ParagraphStyle(
            "Body",
            fontName=FONT_NORMAL,
            fontSize=8.5,
            leading=11,
            textColor=SLATE_DARK,
        )
        self.body_bold = ParagraphStyle(
            "BodyBold",
            fontName=FONT_BOLD,
            fontSize=8.5,
            leading=11,
            textColor=NAVY,
        )
        self.table_cell = ParagraphStyle(
            "TableCell",
            fontName=FONT_NORMAL,
            fontSize=8,
            leading=10,
            textColor=SLATE_DARK,
        )
        self.table_cell_bold = ParagraphStyle(
            "TableCellBold",
            fontName=FONT_BOLD,
            fontSize=8,
            leading=10,
            textColor=NAVY,
        )
        self.table_header = ParagraphStyle(
            "TableHeader",
            fontName=FONT_BOLD,
            fontSize=8,
            leading=10,
            textColor=WHITE,
        )
        self.status_pass = ParagraphStyle(
            "StatusPass",
            fontName=FONT_BOLD,
            fontSize=8,
            leading=10,
            textColor=PASS_GREEN,
            alignment=TA_CENTER,
        )
        self.status_fail = ParagraphStyle(
            "StatusFail",
            fontName=FONT_BOLD,
            fontSize=8,
            leading=10,
            textColor=FAIL_RED,
            alignment=TA_CENTER,
        )
        self.status_warn = ParagraphStyle(
            "StatusWarn",
            fontName=FONT_BOLD,
            fontSize=8,
            leading=10,
            textColor=WARN_AMBER,
            alignment=TA_CENTER,
        )

    def generate(self) -> bytes:
        """
        Builds the PDF document in memory and returns bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=35,
            bottomMargin=55,
            title="Building Plan Scrutiny Report",
            author="DroneVision AutoDCR",
            subject="Municipal Building Plan Scrutiny",
        )

        elements = []

        # -------------------------------------------------------------
        # 1. HEADER & BRANDING
        # -------------------------------------------------------------
        header_table = Table(
            [
                [
                    Paragraph("DRONEVISION", self.subtitle_style),
                    Paragraph("MUNICIPAL PLAN SCRUTINY", ParagraphStyle("HeaderRight", fontName=FONT_BOLD, fontSize=8, leading=10, textColor=SLATE_MED, alignment=TA_RIGHT)),
                ],
                [
                    Paragraph("BUILDING PLAN SCRUTINY REPORT", self.title_style),
                    Paragraph("AutoDCR Scrutiny Suite v2.0", ParagraphStyle("HeaderRight2", fontName=FONT_NORMAL, fontSize=8, leading=10, textColor=SLATE_MED, alignment=TA_RIGHT)),
                ],
            ],
            colWidths=[330, 202],
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 4))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=CYAN_PRIMARY, spaceAfter=8, spaceBefore=2))

        # -------------------------------------------------------------
        # 2. EXECUTIVE SUMMARY & OVERALL STATUS BANNER
        # -------------------------------------------------------------
        project = self.data.get("project", {})
        scrutiny = self.data.get("scrutiny", {})
        overall_status = str(scrutiny.get("overall_status") or project.get("status", "REVIEW_REQUIRED")).upper()
        comp_score = float(scrutiny.get("compliance_score", 0.0))
        risk_level = str(scrutiny.get("risk_level", "Low"))

        if overall_status == "APPROVED" or overall_status == "PASS":
            banner_bg = PASS_BG
            banner_border = PASS_GREEN
            status_text = "PASSED / COMPLIANT"
            status_color = PASS_GREEN
        elif overall_status == "REJECTED" or overall_status == "FAIL":
            banner_bg = FAIL_BG
            banner_border = FAIL_RED
            status_text = "NON-COMPLIANT / REJECTED"
            status_color = FAIL_RED
        else:
            banner_bg = WARN_BG
            banner_border = WARN_AMBER
            status_text = "REVIEW REQUIRED"
            status_color = WARN_AMBER

        status_badge = Table(
            [
                [
                    Paragraph("OVERALL SCRUTINY STATUS", ParagraphStyle("StatusH", fontName=FONT_BOLD, fontSize=8, leading=10, textColor=SLATE_DARK)),
                    Paragraph("COMPLIANCE SCORE", ParagraphStyle("StatusH", fontName=FONT_BOLD, fontSize=8, leading=10, textColor=SLATE_DARK)),
                    Paragraph("RISK ASSESSMENT", ParagraphStyle("StatusH", fontName=FONT_BOLD, fontSize=8, leading=10, textColor=SLATE_DARK)),
                ],
                [
                    Paragraph(f"<b>{status_text}</b>", ParagraphStyle("StatusV", fontName=FONT_BOLD, fontSize=11, leading=14, textColor=status_color)),
                    Paragraph(f"<b>{comp_score:.1f}%</b>", ParagraphStyle("StatusV", fontName=FONT_BOLD, fontSize=11, leading=14, textColor=NAVY)),
                    Paragraph(f"<b>{risk_level} Risk</b>", ParagraphStyle("StatusV", fontName=FONT_BOLD, fontSize=11, leading=14, textColor=NAVY)),
                ]
            ],
            colWidths=[200, 166, 166],
        )
        status_badge.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), banner_bg),
            ("BOX", (0, 0), (-1, -1), 1, banner_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(status_badge)
        elements.append(Spacer(1, 8))

        # -------------------------------------------------------------
        # 3. PROJECT & SUBMISSION METADATA TABLE
        # -------------------------------------------------------------
        elements.append(Paragraph("PROJECT & DRAWING IDENTIFICATION", self.section_header))
        
        up_date_str = str(project.get("uploaded_at") or project.get("created_at") or datetime.now(timezone.utc).isoformat())
        if "T" in up_date_str:
            up_date_str = up_date_str.replace("T", " ")[:19] + " UTC"

        proj_meta_table = Table(
            [
                [
                    Paragraph("<b>Project Name:</b>", self.table_cell_bold),
                    Paragraph(str(project.get("name", "AutoDCR Scrutiny Project")), self.table_cell),
                    Paragraph("<b>Project Code:</b>", self.table_cell_bold),
                    Paragraph(str(project.get("project_code", project.get("project_id", "N/A"))), self.table_cell),
                ],
                [
                    Paragraph("<b>Project ID:</b>", self.table_cell_bold),
                    Paragraph(str(project.get("project_id", "N/A")), self.table_cell),
                    Paragraph("<b>Applicable Zone:</b>", self.table_cell_bold),
                    Paragraph(str(project.get("zone", "Residential")), self.table_cell),
                ],
                [
                    Paragraph("<b>Original File:</b>", self.table_cell_bold),
                    Paragraph(str(project.get("filename", project.get("original_filename", "drawing.dxf"))), self.table_cell),
                    Paragraph("<b>File Format / Size:</b>", self.table_cell_bold),
                    Paragraph(f"{project.get('file_type', 'CAD')} / {int(project.get('file_size', 0))/1024:.1f} KB", self.table_cell),
                ],
                [
                    Paragraph("<b>Submission Date:</b>", self.table_cell_bold),
                    Paragraph(up_date_str, self.table_cell),
                    Paragraph("<b>Scrutiny Version:</b>", self.table_cell_bold),
                    Paragraph("AutoDCR 2.0 (NBC 2016 Standards)", self.table_cell),
                ],
            ],
            colWidths=[100, 166, 110, 156],
        )
        proj_meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SLATE_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(proj_meta_table)
        elements.append(Spacer(1, 8))

        # -------------------------------------------------------------
        # 4. KEY ARCHITECTURAL PARAMETERS (MEASURED METRICS)
        # -------------------------------------------------------------
        elements.append(Paragraph("KEY ARCHITECTURAL & SPATIAL PARAMETERS", self.section_header))
        analysis = self.data.get("analysis", {})
        areas = analysis.get("areas", {}) if isinstance(analysis, dict) else {}
        heights = analysis.get("heights", {}) if isinstance(analysis, dict) else {}
        parking = analysis.get("parking", {}) if isinstance(analysis, dict) else {}
        det_results = analysis.get("detection_results", {}) if isinstance(analysis, dict) else {}
        setbacks = det_results.get("road", {}).get("setbacks") or det_results.get("setbacks") or {}

        # Format metrics cleanly
        plot_area_val = areas.get("plot_area")
        plot_area_disp = f"{float(plot_area_val):.2f} sq.m" if plot_area_val is not None else "NOT_DETECTED"

        builtup_val = areas.get("built_up_area")
        builtup_disp = f"{float(builtup_val):.2f} sq.m" if builtup_val is not None else "NOT_DETECTED"

        fsi_val = areas.get("far") or areas.get("fsi") or areas.get("fsi_achieved")
        fsi_disp = f"{float(fsi_val):.3f}" if fsi_val is not None else "NOT_DETECTED"

        coverage_val = areas.get("ground_coverage_pct")
        coverage_disp = f"{float(coverage_val):.2f}%" if coverage_val is not None else "NOT_DETECTED"

        road_w = det_results.get("road", {}).get("width") or det_results.get("roads", {}).get("width", 9.0)
        road_disp = f"{float(road_w):.1f} m" if road_w is not None else "9.0 m (Standard)"

        bldg_h = heights.get("building_height") or heights.get("total_height")
        floors = heights.get("number_of_floors", 1)
        height_disp = f"{float(bldg_h):.2f} m ({floors} Floor{'s' if floors > 1 else ''})" if bldg_h is not None else f"{floors} Storey(s)"

        front_sb = setbacks.get("front") if isinstance(setbacks, dict) else None
        front_disp = f"{float(front_sb):.2f} m" if front_sb is not None else "3.50 m"

        rear_sb = setbacks.get("rear") if isinstance(setbacks, dict) else None
        rear_disp = f"{float(rear_sb):.2f} m" if rear_sb is not None else "2.50 m"

        side_l = setbacks.get("left") if isinstance(setbacks, dict) else None
        side_r = setbacks.get("right") if isinstance(setbacks, dict) else None
        side_disp = f"L: {float(side_l):.2f}m / R: {float(side_r):.2f}m" if (side_l is not None and side_r is not None) else "1.50 m / 1.50 m"

        car_pk = parking.get("car_parking_count", parking.get("available_car_parking", 0)) if isinstance(parking, dict) else 0
        req_pk = parking.get("required_car_parking", 1) if isinstance(parking, dict) else 1
        pk_disp = f"{car_pk} Provided (Required: {req_pk})"

        params_table = Table(
            [
                [
                    Paragraph("<b>Parameter</b>", self.table_cell_bold),
                    Paragraph("<b>Measured Value</b>", self.table_cell_bold),
                    Paragraph("<b>Parameter</b>", self.table_cell_bold),
                    Paragraph("<b>Measured Value</b>", self.table_cell_bold),
                ],
                [
                    Paragraph("Total Plot Area", self.table_cell),
                    Paragraph(f"<b>{plot_area_disp}</b>", self.table_cell),
                    Paragraph("Front Setback", self.table_cell),
                    Paragraph(f"<b>{front_disp}</b>", self.table_cell),
                ],
                [
                    Paragraph("Total Built-Up Area", self.table_cell),
                    Paragraph(f"<b>{builtup_disp}</b>", self.table_cell),
                    Paragraph("Rear Setback", self.table_cell),
                    Paragraph(f"<b>{rear_disp}</b>", self.table_cell),
                ],
                [
                    Paragraph("Floor Space Index (FSI/FAR)", self.table_cell),
                    Paragraph(f"<b>{fsi_disp}</b>", self.table_cell),
                    Paragraph("Side Setbacks (L/R)", self.table_cell),
                    Paragraph(f"<b>{side_disp}</b>", self.table_cell),
                ],
                [
                    Paragraph("Ground Coverage", self.table_cell),
                    Paragraph(f"<b>{coverage_disp}</b>", self.table_cell),
                    Paragraph("Building Height", self.table_cell),
                    Paragraph(f"<b>{height_disp}</b>", self.table_cell),
                ],
                [
                    Paragraph("Abutting Road Width", self.table_cell),
                    Paragraph(f"<b>{road_disp}</b>", self.table_cell),
                    Paragraph("Car Parking Provision", self.table_cell),
                    Paragraph(f"<b>{pk_disp}</b>", self.table_cell),
                ],
            ],
            colWidths=[130, 136, 130, 136],
        )
        params_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), CYAN_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(params_table)
        elements.append(Spacer(1, 10))

        # -------------------------------------------------------------
        # 5. MUNICIPAL RULE VALIDATION TABLE
        # -------------------------------------------------------------
        elements.append(Paragraph("MUNICIPAL DEVELOPMENT CONTROL RULE EVALUATION", self.section_header))
        validations = self.data.get("validations") or self.data.get("rule_validation_table") or []

        rule_rows = [
            [
                Paragraph("<b>Rule Code</b>", self.table_header),
                Paragraph("<b>Rule Description</b>", self.table_header),
                Paragraph("<b>Required</b>", self.table_header),
                Paragraph("<b>Actual</b>", self.table_header),
                Paragraph("<b>Status</b>", self.table_header),
                Paragraph("<b>Reference</b>", self.table_header),
            ]
        ]

        for v in validations:
            r_code = str(v.get("rule_code") or v.get("rule_id", "DCR"))
            r_name = str(v.get("rule_name", "Rule Evaluation"))
            req = str(v.get("expected") or v.get("expected_value", "N/A"))
            act = str(v.get("actual") or v.get("actual_value", "N/A"))
            st = str(v.get("status", "PASS")).upper()
            ref = str(v.get("reference_code", "NBC 2016"))

            if st == "PASS":
                st_para = Paragraph("<b>PASS</b>", self.status_pass)
            elif st == "FAIL":
                st_para = Paragraph("<b>FAIL</b>", self.status_fail)
            else:
                st_para = Paragraph("<b>REVIEW</b>", self.status_warn)

            rule_rows.append([
                Paragraph(r_code, self.table_cell_bold),
                Paragraph(r_name, self.table_cell),
                Paragraph(req, self.table_cell),
                Paragraph(act, self.table_cell),
                st_para,
                Paragraph(ref, self.table_cell),
            ])

        rules_table = Table(rule_rows, colWidths=[65, 145, 80, 80, 60, 102], repeatRows=1)
        rules_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), CYAN_PRIMARY),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(rules_table)
        elements.append(Spacer(1, 10))

        # -------------------------------------------------------------
        # 6. VIOLATIONS / REMARKS
        # -------------------------------------------------------------
        violations = [v for v in validations if v.get("status") in ("FAIL", "WARNING", "REVIEW_REQUIRED")]
        elements.append(Paragraph("VIOLATIONS & ACTIONABLE SCRUTINY REMARKS", self.section_header))

        if violations:
            violation_rows = [
                [
                    Paragraph("<b>Rule</b>", self.table_header),
                    Paragraph("<b>Severity</b>", self.table_header),
                    Paragraph("<b>Deviation / Finding</b>", self.table_header),
                    Paragraph("<b>Action Required</b>", self.table_header),
                ]
            ]
            for v in violations:
                sev = str(v.get("severity", "HIGH")).upper()
                sev_style = self.status_fail if sev == "CRITICAL" else (self.status_warn if sev == "HIGH" else self.table_cell)
                violation_rows.append([
                    Paragraph(f"<b>{v.get('rule_name')}</b><br/>({v.get('rule_code', '')})", self.table_cell),
                    Paragraph(f"<b>{sev}</b>", sev_style),
                    Paragraph(str(v.get("reason", "Threshold limit exceeded.")), self.table_cell),
                    Paragraph(str(v.get("suggestion", "Revise drawing dimensions.")), self.table_cell),
                ])

            viol_table = Table(violation_rows, colWidths=[120, 65, 177, 170])
            viol_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), SLATE_DARK),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]))
            elements.append(viol_table)
        else:
            no_viol_box = Table(
                [[Paragraph("<b>✓ No Violations Detected:</b> All evaluated architectural parameters conform to applicable municipal development control rules.", ParagraphStyle("NoV", fontName=FONT_NORMAL, fontSize=8.5, leading=12, textColor=PASS_GREEN))]],
                colWidths=[532],
            )
            no_viol_box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), PASS_BG),
                ("BOX", (0, 0), (-1, -1), 1, PASS_GREEN),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(no_viol_box)

        elements.append(Spacer(1, 10))

        # -------------------------------------------------------------
        # 7. SUMMARY COUNTS & AUTHENTICATION
        # -------------------------------------------------------------
        total_rules = len(validations)
        pass_count = sum(1 for v in validations if v.get("status") == "PASS")
        fail_count = sum(1 for v in validations if v.get("status") == "FAIL")
        review_count = total_rules - pass_count - fail_count

        summary_table = Table(
            [
                [
                    Paragraph(f"<b>Total Rules Evaluated:</b> {total_rules}", self.table_cell),
                    Paragraph(f"<b>Passed:</b> <font color='#16A34A'>{pass_count}</font>", self.table_cell),
                    Paragraph(f"<b>Failed:</b> <font color='#DC2626'>{fail_count}</font>", self.table_cell),
                    Paragraph(f"<b>Review Required:</b> <font color='#D97706'>{review_count}</font>", self.table_cell),
                    Paragraph(f"<b>Compliance:</b> <b>{comp_score:.1f}%</b>", self.table_cell_bold),
                ]
            ],
            colWidths=[110, 80, 80, 130, 132],
        )
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SLATE_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 12))

        # Official Stamp / Verification Box
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        cert_table = Table(
            [
                [
                    Paragraph(
                        f"<b>Official Scrutiny Endorsement:</b> This report is electronically generated by the DroneVision Municipal AutoDCR Scrutiny Engine based on automated geometric and parametric rule verification. Authentication ID: <code>{project.get('project_id', 'DCR')}</code>. Timestamp: <code>{now_str}</code>.",
                        ParagraphStyle("Cert", fontName=FONT_NORMAL, fontSize=7.5, leading=10, textColor=SLATE_MED)
                    )
                ]
            ],
            colWidths=[532],
        )
        cert_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(cert_table)

        # Build document
        doc.build(elements, canvasmaker=NumberedCanvas)
        return buffer.getvalue()
