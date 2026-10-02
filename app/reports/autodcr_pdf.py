import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

try:
    pdfmetrics.registerFont(TTFont('SegoeUI', 'C:/Windows/Fonts/segoeui.ttf'))
    pdfmetrics.registerFont(TTFont('SegoeUI-Bold', 'C:/Windows/Fonts/segoeuib.ttf'))
    DEFAULT_FONT = 'SegoeUI'
    BOLD_FONT = 'SegoeUI-Bold'
except Exception:
    DEFAULT_FONT = 'Helvetica'
    BOLD_FONT = 'Helvetica-Bold'

NAVY = colors.HexColor('#0F172A')
CYAN = colors.HexColor('#0891B2')
CYAN_LIGHT = colors.HexColor('#ECFEFF')
SLATE_DARK = colors.HexColor('#1E293B')
SLATE = colors.HexColor('#475569')
SLATE_LIGHT = colors.HexColor('#94A3B8')
PANEL_BG = colors.HexColor('#F8FAFC')
BORDER_COLOR = colors.HexColor('#E2E8F0')
EMERALD = colors.HexColor('#059669')
EMERALD_BG = colors.HexColor('#ECFDF5')
AMBER = colors.HexColor('#D97706')
AMBER_BG = colors.HexColor('#FFFBEB')
ROSE = colors.HexColor('#E11D48')
ROSE_BG = colors.HexColor('#FFF1F2')

class AutoDCRPDFGenerator:
    def __init__(self, report_data: Dict[str, Any]):
        self.data = report_data
        self._build_styles()

    def _build_styles(self):
        base = getSampleStyleSheet()

        self.title_style = ParagraphStyle(
            'DocTitle',
            parent=base['Normal'],
            fontName=BOLD_FONT,
            fontSize=15,
            leading=18,
            textColor=NAVY,
            alignment=TA_LEFT,
        )

        self.subtitle_style = ParagraphStyle(
            'DocSubTitle',
            parent=base['Normal'],
            fontName=DEFAULT_FONT,
            fontSize=8,
            leading=11,
            textColor=SLATE,
            alignment=TA_LEFT,
        )

        self.govt_style = ParagraphStyle(
            'GovtHeading',
            parent=base['Normal'],
            fontName=BOLD_FONT,
            fontSize=8,
            leading=10,
            textColor=CYAN,
            alignment=TA_LEFT,
        )

        self.section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=base['Normal'],
            fontName=BOLD_FONT,
            fontSize=10,
            leading=13,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=4,
        )

        self.cell_label_style = ParagraphStyle(
            'CellLabel',
            parent=base['Normal'],
            fontName=DEFAULT_FONT,
            fontSize=7.5,
            leading=9.5,
            textColor=SLATE,
        )

        self.cell_val_style = ParagraphStyle(
            'CellVal',
            parent=base['Normal'],
            fontName=BOLD_FONT,
            fontSize=8.5,
            leading=11,
            textColor=NAVY,
        )

        self.table_header_style = ParagraphStyle(
            'TableHeader',
            parent=base['Normal'],
            fontName=BOLD_FONT,
            fontSize=8,
            leading=10,
            textColor=NAVY,
            alignment=TA_LEFT,
        )

        self.table_cell_style = ParagraphStyle(
            'TableCell',
            parent=base['Normal'],
            fontName=DEFAULT_FONT,
            fontSize=7.5,
            leading=9.5,
            textColor=SLATE_DARK,
            alignment=TA_LEFT,
        )

        self.table_cell_bold = ParagraphStyle(
            'TableCellBold',
            parent=base['Normal'],
            fontName=BOLD_FONT,
            fontSize=7.5,
            leading=9.5,
            textColor=NAVY,
            alignment=TA_LEFT,
        )

        self.badge_pass_style = ParagraphStyle(
            'BadgePass',
            parent=base['Normal'],
            fontName=BOLD_FONT,
            fontSize=7.5,
            leading=9.5,
            textColor=EMERALD,
            alignment=TA_CENTER,
        )

        self.badge_fail_style = ParagraphStyle(
            'BadgeFail',
            parent=base['Normal'],
            fontName=BOLD_FONT,
            fontSize=7.5,
            leading=9.5,
            textColor=ROSE,
            alignment=TA_CENTER,
        )

        self.badge_warn_style = ParagraphStyle(
            'BadgeWarn',
            parent=base['Normal'],
            fontName=BOLD_FONT,
            fontSize=7.5,
            leading=9.5,
            textColor=AMBER,
            alignment=TA_CENTER,
        )

    def _draw_page_decorations(self, canvas, doc):
        width, height = doc.pagesize
        canvas.saveState()

        canvas.setFillColor(NAVY)
        canvas.rect(0, height - 36, width, 36, stroke=0, fill=1)
        canvas.setFillColor(CYAN)
        canvas.rect(0, height - 36, 6, 36, stroke=0, fill=1)

        canvas.setFont(BOLD_FONT, 11)
        canvas.setFillColor(colors.white)
        canvas.drawString(24, height - 23, 'DRONEVISION AUTODCR')

        canvas.setFont(DEFAULT_FONT, 7.5)
        canvas.setFillColor(colors.HexColor('#A5F3FC'))
        canvas.drawString(180, height - 22, 'Automated Development Control Regulations Scrutiny Engine')

        proj_code = self.data.get('project_code') or self.data.get('project_id', '-')
        canvas.setFont(BOLD_FONT, 8)
        canvas.setFillColor(colors.white)
        canvas.drawRightString(width - 24, height - 23, f'Project: {proj_code}')

        canvas.setStrokeColor(BORDER_COLOR)
        canvas.setLineWidth(0.6)
        canvas.line(24, 28, width - 24, 28)

        canvas.setFont(DEFAULT_FONT, 7)
        canvas.setFillColor(SLATE_LIGHT)
        canvas.drawString(24, 16, 'Government Town Planning Department  •  AutoDCR Scrutiny Suite  •  Confidential Official Document')
        canvas.drawRightString(width - 24, 16, f'Page {doc.page}')

        canvas.restoreState()

    def generate_pdf_bytes(self) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=24,
            rightMargin=24,
            topMargin=46,
            bottomMargin=36,
        )

        story = []
        summary = self.data.get('summary', {})
        status = summary.get('overall_status') or self.data.get('status', 'REVIEW_REQUIRED')
        comp_pct = summary.get('compliance_percentage', self.data.get('compliance_percentage', 0.0))

        badge_bg = EMERALD_BG if status == 'APPROVED' else (ROSE_BG if status in ['FAILED', 'REJECTED'] else AMBER_BG)
        badge_color = EMERALD if status == 'APPROVED' else (ROSE if status in ['FAILED', 'REJECTED'] else AMBER)
        badge_text = f'SCRUTINY {status}'

        header_left = [
            Paragraph('GOVERNMENT OF TELANGANA / MUNICIPAL CORPORATION', self.govt_style),
            Spacer(1, 2),
            Paragraph('BUILDING PLAN SCRUTINY APPROVAL REPORT', self.title_style),
            Spacer(1, 2),
            Paragraph(
                'Issued under the provisions of Telangana Municipalities Act & National Building Code (NBC 2016)',
                self.subtitle_style
            ),
        ]

        status_box = Table(
            [
                [Paragraph(f'<b>{badge_text}</b>', ParagraphStyle('HBadge', parent=self.badge_pass_style, textColor=badge_color, fontSize=9))],
                [Paragraph(f'Compliance: {comp_pct:.1f}%', ParagraphStyle('HComp', parent=self.subtitle_style, alignment=TA_CENTER, textColor=badge_color, fontSize=7.5))],
            ],
            colWidths=[1.8 * inch],
        )
        status_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), badge_bg),
            ('BOX', (0, 0), (-1, -1), 1, badge_color),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))

        header_table = Table([[header_left, status_box]], colWidths=[5.4 * inch, 2.0 * inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width='100%', thickness=1, color=NAVY, spaceAfter=8))

        uploaded_str = self.data.get('uploaded_at', '-')
        if uploaded_str and 'T' in str(uploaded_str):
            uploaded_str = str(uploaded_str).replace('T', ' ')[:19]

        analyzed_str = self.data.get('analyzed_at', self.data.get('generated_at', '-'))
        if analyzed_str and 'T' in str(analyzed_str):
            analyzed_str = str(analyzed_str).replace('T', ' ')[:19]

        meta_grid = [
            [
                Paragraph('<b>PROJECT ID</b>', self.cell_label_style),
                Paragraph('<b>ORIGINAL FILE</b>', self.cell_label_style),
                Paragraph('<b>ZONING CATEGORY</b>', self.cell_label_style),
                Paragraph('<b>UPLOADED DATE</b>', self.cell_label_style),
            ],
            [
                Paragraph(self.data.get('project_id', '-'), self.cell_val_style),
                Paragraph(self.data.get('original_filename', '-'), self.cell_val_style),
                Paragraph(self.data.get('zone', 'Residential'), self.cell_val_style),
                Paragraph(str(uploaded_str), self.cell_val_style),
            ],
            [
                Paragraph('<b>APPLICANT / OWNER</b>', self.cell_label_style),
                Paragraph('<b>PLOT NUMBER</b>', self.cell_label_style),
                Paragraph('<b>TOTAL RULES EVALUATED</b>', self.cell_label_style),
                Paragraph('<b>ANALYSIS TIMESTAMP</b>', self.cell_label_style),
            ],
            [
                Paragraph(self.data.get('applicant_name') or 'Municipal Applicant', self.cell_val_style),
                Paragraph(self.data.get('plot_number') or '-', self.cell_val_style),
                Paragraph(str(summary.get('total_rules', len(self.data.get('rules', [])))), self.cell_val_style),
                Paragraph(str(analyzed_str), self.cell_val_style),
            ],
        ]

        meta_table = Table(meta_grid, colWidths=[1.85 * inch, 2.0 * inch, 1.7 * inch, 1.85 * inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), PANEL_BG),
            ('BOX', (0, 0), (-1, -1), 0.6, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.4, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        story.append(Paragraph('KEY ARCHITECTURAL & SPATIAL PARAMETERS', self.section_title_style))

        areas = self.data.get('architectural_parameters') or summary
        p_area = areas.get('plot_area')
        b_area = areas.get('built_up_area')
        cov_pct = areas.get('ground_coverage_pct')
        fsi_val = areas.get('fsi', areas.get('fsi_achieved', areas.get('far', areas.get('far_achieved'))))
        fsi_perm = areas.get('fsi_permissible', 2.5)
        height = areas.get('building_height')
        floors = areas.get('floor_count', 1)
        open_area = areas.get('open_area', areas.get('open_space_area'))
        parking = self.data.get('parking', {})

        p_str = f'{float(p_area):.2f} sq.m' if p_area is not None else 'Not detected'
        b_str = f'{float(b_area):.2f} sq.m' if b_area is not None else 'Not detected'
        cov_str = f'{float(cov_pct):.2f}%' if cov_pct is not None else 'Not detected'
        fsi_str = f'{float(fsi_val):.3f}' if fsi_val is not None else 'Not detected'
        perm_str = f'{float(fsi_perm):.2f}'
        h_str = f'{float(height):.2f} m ({floors} Floors)' if height is not None else f'{floors} Floors'
        op_str = f'{float(open_area):.2f} sq.m' if open_area is not None else 'Not detected'

        req_park = parking.get('required_car_parking', parking.get('required_slots', '-'))
        prov_park = parking.get('available_car_parking', parking.get('provided_slots', '-'))
        park_str = f'Provided: {prov_park} / Required: {req_park}'

        params_data = [
            [
                Paragraph('<b>Total Plot Area:</b>', self.table_cell_style), Paragraph(p_str, self.table_cell_bold),
                Paragraph('<b>Total Built-up Area:</b>', self.table_cell_style), Paragraph(b_str, self.table_cell_bold),
            ],
            [
                Paragraph('<b>Ground Coverage:</b>', self.table_cell_style), Paragraph(cov_str, self.table_cell_bold),
                Paragraph('<b>FSI Achieved / Max:</b>', self.table_cell_style), Paragraph(f'{fsi_str} (Max {perm_str})', self.table_cell_bold),
            ],
            [
                Paragraph('<b>Building Height:</b>', self.table_cell_style), Paragraph(h_str, self.table_cell_bold),
                Paragraph('<b>Open Space Area:</b>', self.table_cell_style), Paragraph(op_str, self.table_cell_bold),
            ],
            [
                Paragraph('<b>Car Parking:</b>', self.table_cell_style), Paragraph(str(park_str), self.table_cell_bold),
                Paragraph('<b>Evaluation Zone:</b>', self.table_cell_style), Paragraph(self.data.get('zone', 'Residential'), self.table_cell_bold),
            ],
        ]

        params_table = Table(params_data, colWidths=[1.85 * inch, 1.85 * inch, 1.85 * inch, 1.85 * inch])
        params_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), PANEL_BG),
            ('BOX', (0, 0), (-1, -1), 0.6, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.4, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(params_table)
        story.append(Spacer(1, 10))

        story.append(Paragraph('MUNICIPAL DEVELOPMENT CONTROL REGULATIONS SCRUTINY MATRIX', self.section_title_style))

        rules = self.data.get('rules') or self.data.get('validations') or []
        rule_rows = [
            [
                Paragraph('<b>Rule & Parameter</b>', self.table_header_style),
                Paragraph('<b>Category</b>', self.table_header_style),
                Paragraph('<b>Requirement</b>', self.table_header_style),
                Paragraph('<b>Actual Computed</b>', self.table_header_style),
                Paragraph('<b>Status</b>', ParagraphStyle('THC', parent=self.table_header_style, alignment=TA_CENTER)),
                Paragraph('<b>Remarks / Reference</b>', self.table_header_style),
            ]
        ]

        for r in rules:
            r_name = r.get('rule_name') or r.get('name') or 'Bylaw Regulation'
            cat = r.get('category') or 'General'
            req = str(r.get('expected') or r.get('expected_value') or r.get('min_value') or '-')
            act = str(r.get('actual') or r.get('actual_value') or '-')
            st = str(r.get('status') or 'PASS').upper()
            rem = str(r.get('reason') or r.get('suggestion') or r.get('reference_code') or 'Compliant with NBC 2016')

            st_style = self.badge_pass_style if st == 'PASS' else (self.badge_fail_style if st == 'FAIL' else self.badge_warn_style)
            rule_rows.append([
                Paragraph(r_name, self.table_cell_bold),
                Paragraph(cat, self.table_cell_style),
                Paragraph(req, self.table_cell_style),
                Paragraph(act, self.table_cell_bold),
                Paragraph(f'<b>{st}</b>', st_style),
                Paragraph(rem, self.table_cell_style),
            ])

        rule_table = Table(
            rule_rows,
            colWidths=[1.8 * inch, 0.9 * inch, 1.2 * inch, 1.1 * inch, 0.8 * inch, 1.6 * inch]
        )
        rule_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('BOX', (0, 0), (-1, -1), 0.6, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.4, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(rule_table)
        story.append(Spacer(1, 10))

        violations = self.data.get('violations', [])
        if not violations:
            violations = [r for r in rules if r.get('status') == 'FAIL']

        if violations:
            story.append(Paragraph('VIOLATIONS & NON-COMPLIANCE SUMMARY', self.section_title_style))
            v_rows = []
            for v in violations:
                v_name = v.get('rule_name') or 'Violation'
                reason = v.get('reason') or v.get('suggestion') or 'Parameters violate mandated municipal thresholds.'
                v_rows.append([
                    Paragraph(f'• <b>{v_name}</b>: {reason}', self.table_cell_style)
                ])
            v_table = Table(v_rows, colWidths=[7.4 * inch])
            v_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), ROSE_BG),
                ('BOX', (0, 0), (-1, -1), 0.6, ROSE),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(v_table)
            story.append(Spacer(1, 10))
        else:
            story.append(Paragraph('VIOLATIONS & NON-COMPLIANCE SUMMARY', self.section_title_style))
            no_v_table = Table([[Paragraph('<b>No violations detected.</b> All tested geometric and zoning parameters satisfy applicable development control regulations.', self.table_cell_style)]], colWidths=[7.4 * inch])
            no_v_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), EMERALD_BG),
                ('BOX', (0, 0), (-1, -1), 0.6, EMERALD),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(no_v_table)
            story.append(Spacer(1, 10))

        auth_box = [
            Paragraph('<b>ELECTRONIC SCRUTINY AUTHENTICATION SEAL</b>', self.cell_label_style),
            Paragraph(
                'This document is an electronically authenticated Scrutiny Certificate generated by the DroneVision Municipal AutoDCR Engine v2.0.0. '
                'Calculations are strictly computed from uploaded vector & geometric drawing entities in compliance with statutory NBC/Telangana bylaws.',
                self.subtitle_style
            ),
        ]
        auth_table = Table([[auth_box]], colWidths=[7.4 * inch])
        auth_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), PANEL_BG),
            ('BOX', (0, 0), (-1, -1), 0.6, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(auth_table)

        doc.build(story, onFirstPage=self._draw_page_decorations, onLaterPages=self._draw_page_decorations)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
