"""
Visualization Engine module for AutoDCR.
Generates annotated SVG/PNG CAD drawing previews, colored violation overlays,
dimension labels, and rule measurement overlays for municipal review.
"""

from typing import Dict, Any, List


class VisualizationEngine:
    """
    SVG / PNG Drawing preview & violation overlay generator.
    """

    @staticmethod
    def generate_svg_overlay(
        parsed_data: Dict[str, Any],
        validations: List[Dict[str, Any]],
        width: int = 800,
        height: int = 600
    ) -> str:
        """
        Renders a color-coded SVG visualization of the CAD drawing with rule violation overlays.
        """
        entities = parsed_data.get("entities", {})
        polylines = entities.get("polylines", [])
        lines = entities.get("lines", [])

        svg_lines: List[str] = []
        svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background-color: #1e1e1e;">')
        
        # Grid lines / Background overlay
        svg_lines.append('<g id="background-grid" stroke="#333" stroke-width="0.5">')
        svg_lines.append(f'<line x1="0" y1="{height/2}" x2="{width}" y2="{height/2}"/>')
        svg_lines.append(f'<line x1="{width/2}" y1="0" x2="{width/2}" y2="{height}"/>')
        svg_lines.append('</g>')

        # Render CAD Lines (default cyan/white)
        svg_lines.append('<g id="cad-lines" stroke="#00e5ff" stroke-width="1.5" fill="none">')
        for line in lines[:500]:
            p1 = line.get("start", [0, 0])
            p2 = line.get("end", [0, 0])
            svg_lines.append(f'<line x1="{p1[0]}" y1="{p1[1]}" x2="{p2[0]}" y2="{p2[1]}"/>')
        svg_lines.append('</g>')

        # Render Polylines
        svg_lines.append('<g id="cad-polylines" stroke="#00ff88" stroke-width="2" fill="none">')
        for poly in polylines[:200]:
            pts = poly.get("points", [])
            if len(pts) >= 2:
                points_str = " ".join([f"{pt[0]},{pt[1]}" for pt in pts])
                svg_lines.append(f'<polygon points="{points_str}" fill="rgba(0, 255, 136, 0.1)"/>')
        svg_lines.append('</g>')

        # Violation Overlays (Red for FAIL, Yellow for WARNING)
        svg_lines.append('<g id="violations-overlay">')
        for idx, val in enumerate(validations):
            status = val.get("status")
            color = "#ff1744" if status == "FAIL" else "#ffea00" if status == "WARNING" else "#00e676"
            y_pos = 30 + (idx * 25)
            svg_lines.append(f'<text x="20" y="{y_pos}" fill="{color}" font-family="Arial" font-size="14" font-weight="bold">[{status}] {val.get("rule_name")}: {val.get("actual")} (Expected: {val.get("expected")})</text>')
        svg_lines.append('</g>')

        svg_lines.append('</svg>')

        return "\n".join(svg_lines)
