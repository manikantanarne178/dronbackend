from pathlib import Path
import json

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
)

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ----------------------------------------------------------
# Optional Font
# ----------------------------------------------------------

try:
    pdfmetrics.registerFont(TTFont("SegoeUI", "C:/Windows/Fonts/segoeui.ttf"))
    pdfmetrics.registerFont(TTFont("SegoeUI-Bold", "C:/Windows/Fonts/segoeuib.ttf"))
    DEFAULT_FONT = "SegoeUI"
    BOLD_FONT = "SegoeUI-Bold"
except Exception:
    DEFAULT_FONT = "Helvetica"
    BOLD_FONT = "Helvetica-Bold"


# ----------------------------------------------------------
# Palette
# ----------------------------------------------------------

NAVY = colors.HexColor("#0F172A")
SLATE = colors.HexColor("#475569")
LIGHT_SLATE = colors.HexColor("#94A3B8")
BLUE = colors.HexColor("#0EA5E9")
BLUE_DARK = colors.HexColor("#0369A1")
PANEL_BG = colors.HexColor("#F8FAFC")
BORDER = colors.HexColor("#E2E8F0")
WHITE = colors.white

CARD_COLORS = [
    colors.HexColor("#0EA5E9"),
    colors.HexColor("#2563EB"),
    colors.HexColor("#0891B2"),
    colors.HexColor("#16A34A"),
    colors.HexColor("#059669"),
    colors.HexColor("#7C3AED"),
    colors.HexColor("#EA580C"),
    colors.HexColor("#DC2626"),
]


# ==========================================================
# PDF REPORT GENERATOR — ONE PAGE EDITION
# ==========================================================

class PDFReportGenerator:

    def __init__(self, project_dir):

        self.project_dir = Path(project_dir)
        self.metadata_file = self.project_dir / "metadata.json"
        self.images_dir = self.project_dir / "uploaded_images"
        self.screenshots_dir = self.project_dir / "screenshots"
        self.output_pdf = self.project_dir / "report.pdf"

        with open(self.metadata_file, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

# Load rules.json
        self.rules_file = self.project_dir / "rules.json"

        if self.rules_file.exists():
           with open(self.rules_file, "r", encoding="utf-8") as f:
               self.rule_data = json.load(f)
        else:
           self.rule_data = {
        "overall_status": "UNKNOWN",
        "rules": []
    }

        self._build_styles()
    # ----------------------------------------------------------
    # STYLES
    # ----------------------------------------------------------

    def _build_styles(self):

        base = getSampleStyleSheet()

        self.brand_style = ParagraphStyle(
            "Brand", parent=base["Normal"],
            fontName=BOLD_FONT, fontSize=17, leading=19,
            textColor=WHITE, alignment=TA_LEFT,
        )

        self.brand_sub_style = ParagraphStyle(
            "BrandSub", parent=base["Normal"],
            fontName=DEFAULT_FONT, fontSize=8.5, leading=11,
            textColor=colors.HexColor("#DBEAFE"), alignment=TA_LEFT,
        )

        self.header_meta_style = ParagraphStyle(
            "HeaderMeta", parent=base["Normal"],
            fontName=DEFAULT_FONT, fontSize=8.5, leading=12,
            textColor=WHITE, alignment=TA_RIGHT,
        )

        self.section_label_style = ParagraphStyle(
            "SectionLabel", parent=base["Normal"],
            fontName=BOLD_FONT, fontSize=9.5, leading=12,
            textColor=NAVY, alignment=TA_LEFT,
            spaceAfter=4,
        )

        self.info_label_style = ParagraphStyle(
            "InfoLabel", parent=base["Normal"],
            fontName=DEFAULT_FONT, fontSize=8, leading=10,
            textColor=SLATE, alignment=TA_LEFT,
        )

        self.info_value_style = ParagraphStyle(
            "InfoValue", parent=base["Normal"],
            fontName=BOLD_FONT, fontSize=9, leading=11,
            textColor=NAVY, alignment=TA_LEFT,
        )

        self.card_title_style = ParagraphStyle(
            "CardTitle", parent=base["Normal"],
            fontName=DEFAULT_FONT, fontSize=7.3, leading=9,
            textColor=WHITE, alignment=TA_CENTER,
        )

        self.card_value_style = ParagraphStyle(
            "CardValue", parent=base["Normal"],
            fontName=BOLD_FONT, fontSize=13, leading=15,
            textColor=WHITE, alignment=TA_CENTER,
        )

        self.caption_style = ParagraphStyle(
            "Caption", parent=base["Normal"],
            fontName=DEFAULT_FONT, fontSize=6.8, leading=8.5,
            textColor=SLATE, alignment=TA_CENTER,
        )

        self.step_style = ParagraphStyle(
            "Step", parent=base["Normal"],
            fontName=DEFAULT_FONT, fontSize=7.3, leading=9,
            textColor=SLATE, alignment=TA_LEFT,
        )

        self.footer_style = ParagraphStyle(
            "Footer", parent=base["Normal"],
            fontName=DEFAULT_FONT, fontSize=7.5,
            textColor=LIGHT_SLATE,
        )

    # ----------------------------------------------------------
    # HEADER / FOOTER (drawn directly on the canvas)
    # ----------------------------------------------------------

    def _draw_header(self, canvas, doc):

        width, height = doc.pagesize
        band_h = 52

        canvas.saveState()

        # Gradient-ish header band (two-tone rects for a subtle depth effect)
        canvas.setFillColor(NAVY)
        canvas.rect(0, height - band_h, width, band_h, stroke=0, fill=1)
        canvas.setFillColor(BLUE)
        canvas.rect(0, height - band_h, 6, band_h, stroke=0, fill=1)

        canvas.setFont(BOLD_FONT, 16)
        canvas.setFillColor(WHITE)
        canvas.drawString(30, height - 24, "DRONEVISION")

        canvas.setFont(DEFAULT_FONT, 8.5)
        canvas.setFillColor(colors.HexColor("#93C5FD"))
        canvas.drawString(30, height - 37, "AI Drone 3D Mapping Platform  •  3D Reconstruction Report")

        canvas.setFont(BOLD_FONT, 9)
        canvas.setFillColor(WHITE)
        canvas.drawRightString(width - 30, height - 22,
                                f"Project {self.metadata.get('project_id', '-')}")
        canvas.setFont(DEFAULT_FONT, 7.8)
        canvas.setFillColor(colors.HexColor("#93C5FD"))
        canvas.drawRightString(width - 30, height - 34,
                                f"Generated {self.metadata.get('generated_at', '-')}")

        canvas.setFont(BOLD_FONT, 7.5)
        canvas.setFillColor(colors.HexColor("#4ADE80"))
        canvas.drawRightString(width - 30, height - 45, "● STATUS: COMPLETED")

        canvas.restoreState()

    def _draw_footer(self, canvas, doc):

        width, _ = doc.pagesize

        canvas.saveState()
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.6)
        canvas.line(30, 28, width - 30, 28)

        canvas.setFont(DEFAULT_FONT, 7.5)
        canvas.setFillColor(LIGHT_SLATE)
        canvas.drawString(30, 17, "DroneVision  •  AI 3D Mapping Platform  •  Confidential")

        canvas.drawRightString(width - 30, 17, f"Page {doc.page}")
        canvas.restoreState()

    def _page_decorations(self, canvas, doc):
        self._draw_header(canvas, doc)
        self._draw_footer(canvas, doc)

    # ----------------------------------------------------------
    # SMALL HELPERS
    # ----------------------------------------------------------

    def section_label(self, text):
        return Paragraph(text.upper(), self.section_label_style)

    def metric_card(self, title, value, color):
        card = Table(
            [[Paragraph(title, self.card_title_style)],
             [Paragraph(str(value), self.card_value_style)]],
            colWidths=[1.32 * inch],
            rowHeights=[13, 20],
        )
        card.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), color),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.Color(1, 1, 1, alpha=0.25)),
        ]))
        return card

    def _framed(self, flowable, pad=8):
        t = Table([[flowable]], colWidths=[None])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PANEL_BG),
            ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), pad),
            ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
            ("LEFTPADDING", (0, 0), (-1, -1), pad),
            ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ]))
        return t

    # ----------------------------------------------------------
    # BLOCK 1 — Hero image + key info panel
    # ----------------------------------------------------------

    def _hero_and_info(self):

        dims = self.metadata.get("dimensions", {})
        hero_path = self.screenshots_dir / "iso.png"

        if hero_path.exists():
            hero = Image(str(hero_path))
            hero.drawWidth = 2.55 * inch
            hero.drawHeight = 1.85 * inch
        else:
            hero = Paragraph("No preview available", self.caption_style)

        hero_block = Table([[hero]], colWidths=[2.65 * inch], rowHeights=[1.95 * inch])
        hero_block.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ]))

        rows = [
            ("Images Uploaded", str(self.metadata.get("images_uploaded", 0))),
            ("Processing Time", f"{self.metadata.get('processing_time_seconds', '-')} sec"),
            ("Vertices", f"{self.metadata.get('vertices', 0):,}"),
            ("Triangles", f"{self.metadata.get('triangles', 0):,}"),
            ("Dimensions (W×L×H)",
             f"{dims.get('width', 0):.2f} × {dims.get('length', 0):.2f} × {dims.get('height', 0):.2f} m"),
        ]

        info_rows = []
        for label, value in rows:
            info_rows.append([
                Paragraph(label, self.info_label_style),
                Paragraph(value, self.info_value_style),
            ])

        info_table = Table(info_rows, colWidths=[1.55 * inch, 2.0 * inch], rowHeights=21)
        info_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW", (0, 0), (-1, -2), 0.4, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))

        info_panel = self._framed(info_table, pad=7)

        combined = Table(
            [[hero_block, info_panel]],
            colWidths=[2.7 * inch, 3.75 * inch],
        )
        combined.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))

        return [self.section_label("Project Overview"), combined]

    # ----------------------------------------------------------
    # BLOCK 2 — Analytics dashboard (metric cards)
    # ----------------------------------------------------------

    def _analytics_dashboard(self):

        dims = self.metadata.get("dimensions", {})

        metrics = [
            ("Width", f"{dims.get('width', 0):.2f} m"),
            ("Length", f"{dims.get('length', 0):.2f} m"),
            ("Height", f"{dims.get('height', 0):.2f} m"),
            ("Ground Area", f"{self.metadata.get('ground_area', 0):.2f} m²"),
            ("Surface Area", f"{self.metadata.get('surface_area', 0):.2f} m²"),
            ("Volume", f"{self.metadata.get('volume', 0):.2f} m³"),
        ]

        cards = [self.metric_card(t, v, CARD_COLORS[i % len(CARD_COLORS)])
                 for i, (t, v) in enumerate(metrics)]

        row = Table([cards], colWidths=[1.36 * inch] * len(cards))
        row.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))

        return [self.section_label("Analytics Dashboard"), row]

    # ----------------------------------------------------------
    # BLOCK 3 — Model views (front / top / side)
    # ----------------------------------------------------------

    def _model_views(self):

        names = [("front.png", "Front"), ("top.png", "Top"), ("side.png", "Side")]
        cells, captions = [], []

        for fname, label in names:
            path = self.screenshots_dir / fname
            if path.exists():
                img = Image(str(path))
                img.drawWidth = 1.75 * inch
                img.drawHeight = 1.15 * inch
                cells.append(img)
            else:
                cells.append(Paragraph("N/A", self.caption_style))
            captions.append(Paragraph(label, self.caption_style))

        table = Table([cells, captions], colWidths=[1.85 * inch] * 3)
        table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -2), 0.5, BORDER),
            ("INNERGRID", (0, 0), (-1, -2), 0.5, BORDER),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, 0), 4),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            ("TOPPADDING", (0, 1), (-1, 1), 2),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 0),
        ]))

        return [self.section_label("3D Model Views"), table]

    # ----------------------------------------------------------
    # BLOCK 4 — Uploaded image strip
    # ----------------------------------------------------------

    def _image_strip(self, max_images=6):

        images = sorted(self.images_dir.glob("*"))[:max_images]

        if not images:
            return [self.section_label("Uploaded Drone Images"),
                    Paragraph("No uploaded images available.", self.caption_style)]

        cells = []
        for img_path in images:
            try:
                img = Image(str(img_path))
                img.drawWidth = 0.92 * inch
                img.drawHeight = 0.72 * inch
                cells.append(img)
            except Exception:
                cells.append("")

        while len(cells) < max_images:
            cells.append("")

        table = Table([cells], colWidths=[1.0 * inch] * max_images)
        table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))

        total = len(sorted(self.images_dir.glob("*")))
        note = ""
        if total > max_images:
            note = f"  (showing {max_images} of {total})"

        return [self.section_label(f"Uploaded Drone Images{note}"), table]

    # ----------------------------------------------------------
    # BLOCK 5 — Pipeline checklist (compact single line)
    # ----------------------------------------------------------

    def _pipeline_strip(self):

        steps = [
            "Upload", "Feature Extraction", "Feature Matching",
            "Sparse Recon.", "Dense Recon.", "Mesh Gen.",
            "GLB Convert", "Analytics", "Report",
        ]

        text = "   ›   ".join(f"✓ {s}" for s in steps)
        para = Paragraph(text, self.step_style)
        wrapper = self._framed(para, pad=6)

        return [self.section_label("Reconstruction Pipeline"), wrapper]

    # ----------------------------------------------------------
    # BUILD
    # ----------------------------------------------------------

    def generate(self):

        doc = SimpleDocTemplate(
            str(self.output_pdf),
            pagesize=letter,
            rightMargin=30,
            leftMargin=30,
            topMargin=64,
            bottomMargin=38,
        )

        story = []

        story += self._hero_and_info()
        story.append(Spacer(1, 9))

        story += self._analytics_dashboard()
        story.append(Spacer(1, 9))

        story += self._model_views()
        story.append(Spacer(1, 9))

        story += self._image_strip(max_images=6)
        story.append(Spacer(1, 9))

        story += self._pipeline_strip()

        doc.build(
            story,
            onFirstPage=self._page_decorations,
            onLaterPages=self._page_decorations,
        )

        return self.output_pdf


if __name__ == "__main__":
    import sys
    project_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    out = PDFReportGenerator(project_dir).generate()
def _compliance_table(self):

    rows = [
        [
            Paragraph("<b>Rule</b>", self.info_value_style),
            Paragraph("<b>Status</b>", self.info_value_style),
            Paragraph("<b>Actual</b>", self.info_value_style),
            Paragraph("<b>Allowed</b>", self.info_value_style),
        ]
    ]

    for rule in self.rule_data.get("rules", []):

        status = rule.get("status", "-")

        if status.upper() == "PASS":
            color = colors.green
        elif status.upper() == "FAIL":
            color = colors.red
        else:
            color = colors.orange

        rows.append([
            Paragraph(rule.get("rule", "-"), self.info_label_style),
            Paragraph(
                f'<font color="{color.hexval()}"><b>{status}</b></font>',
                self.info_label_style,
            ),
            Paragraph(str(rule.get("actual", "-")), self.info_label_style),
            Paragraph(str(rule.get("allowed", "-")), self.info_label_style),
        ])

    table = Table(
        rows,
        colWidths=[2.2*inch, 1.0*inch, 1.2*inch, 1.2*inch]
    )

    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#E2E8F0")),
        ("BOTTOMPADDING", (0,0), (-1,0), 6),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,1), (-1,-1), 5),
        ("ALIGN", (1,1), (-1,-1), "CENTER"),
    ]))

    overall = Paragraph(
        f"<b>Overall Compliance :</b> {self.rule_data.get('overall_status','UNKNOWN')}",
        self.info_value_style,
    )

    return [
        self.section_label("Compliance Report"),
        table,
        Spacer(1, 8),
        overall,
    ]
    print("Generated:", out)
