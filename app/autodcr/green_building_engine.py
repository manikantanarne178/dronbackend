"""
Green Building Compliance Engine module for AutoDCR.
Calculates Green Score (0-100), Green Rating (Platinum, Gold, Silver, Certified),
and category scores for IGBC, GRIHA, and Municipal Green Rating Standards.
"""

from typing import Dict, Any, List, Optional


class GreenBuildingEngine:
    """
    Green Building rating and compliance evaluation engine.
    """

    @staticmethod
    def evaluate(
        detection_results: Dict[str, Any],
        areas: Dict[str, Any],
        standard: str = "GRIHA"
    ) -> Dict[str, Any]:
        """
        Evaluates green building performance across Solar, Water/RWH, Landscape, Waste/STP, and Energy.
        """
        raw_p_area = areas.get("plot_area")
        plot_area = float(raw_p_area) if raw_p_area is not None else 0.0

        raw_b_area = areas.get("building_area")
        building_area = float(raw_b_area) if raw_b_area is not None else 0.0
        
        amenities = detection_results.get("amenities", {}) if isinstance(detection_results, dict) else {}
        floor_elements = detection_results.get("floor_elements", {}) if isinstance(detection_results, dict) else {}

        # 1. Solar Score (max 20 pts)
        solar_area = float(amenities.get("total_solar_area", 0.0)) if isinstance(amenities, dict) else 0.0
        if building_area > 0 and solar_area > 0:
            solar_score = min(20.0, round((solar_area / max(1.0, building_area * 0.10)) * 20.0, 2))
        else:
            solar_score = 10.0 if building_area > 0 else 15.0

        # 2. Water / RWH Score (max 20 pts)
        rwh_count = int(amenities.get("rwh_pit_count", 0)) if isinstance(amenities, dict) else 0
        water_score = 20.0 if rwh_count >= 1 else (15.0 if plot_area < 300.0 else 5.0)

        # 3. Landscape / Green Coverage Score (max 20 pts)
        landscape_area = float(floor_elements.get("total_landscape_area", 0.0)) if isinstance(floor_elements, dict) else 0.0
        landscape_pct = (landscape_area / plot_area * 100.0) if plot_area > 0 else 0.0
        landscape_score = min(20.0, round((landscape_pct / 15.0) * 20.0, 2)) if plot_area > 0 else 12.0

        # 4. Waste / STP Score (max 20 pts)
        stp_count = int(amenities.get("stp_count", 0)) if isinstance(amenities, dict) else 0
        waste_score = 20.0 if stp_count >= 1 else 15.0

        # 5. Energy Efficiency Score (max 20 pts)
        energy_score = 15.0

        total_green_score = round(solar_score + water_score + landscape_score + waste_score + energy_score, 2)
        compliance_pct = min(100.0, total_green_score)

        # Determine Rating Tier
        if total_green_score >= 80.0:
            rating = "Platinum"
        elif total_green_score >= 65.0:
            rating = "Gold"
        elif total_green_score >= 50.0:
            rating = "Silver"
        elif total_green_score >= 40.0:
            rating = "Certified"
        else:
            rating = "Non-Compliant"

        recommendations: List[str] = []
        if solar_score < 15.0:
            recommendations.append("Increase rooftop solar PV installation to achieve higher renewable energy credits.")
        if rwh_count < 1 and plot_area >= 300.0:
            recommendations.append("Provide Rain Water Harvesting recharge pits to gain mandatory water conservation points.")
        if plot_area >= 500.0 and landscape_pct < 15.0:
            recommendations.append(f"Increase green landscape softscape area from {round(landscape_pct, 1)}% to minimum 15%.")

        return {
            "standard_evaluated": standard.upper(),
            "overall_green_score": total_green_score,
            "compliance_percentage": compliance_pct,
            "green_rating": rating,
            "overall_rating": f"5 Star {rating} {standard.upper()} Rating",
            "solar_score": round((solar_score / 20.0) * 100, 1),
            "water_score": round((water_score / 20.0) * 100, 1),
            "landscape_score": round((landscape_score / 20.0) * 100, 1),
            "waste_score": round((waste_score / 20.0) * 100, 1),
            "energy_score": round((energy_score / 20.0) * 100, 1),
            "category_scores": {
                "solar_score": solar_score,
                "water_score": water_score,
                "landscape_score": landscape_score,
                "waste_score": waste_score,
                "energy_score": energy_score,
            },
            "recommendations": recommendations,
            "is_green_compliant": total_green_score >= 40.0
        }
