"""
Green Building Compliance Engine module for AutoDCR.
Calculates Green Score (0-100), Green Rating (Platinum, Gold, Silver, Certified),
and category scores for IGBC, GRIHA, and Municipal Green Rating Standards.
"""

from typing import Dict, Any, List


class GreenBuildingEngine:
    """
    Green Building rating and compliance evaluation engine.
    """

    @staticmethod
    def evaluate(
        detection_results: Dict[str, Any],
        areas: Dict[str, float],
        standard: str = "GRIHA"
    ) -> Dict[str, Any]:
        """
        Evaluates green building performance across Solar, Water/RWH, Landscape, Waste/STP, and Energy.
        """
        plot_area = areas.get("plot_area", 1.0)
        building_area = areas.get("building_area", 0.0)
        
        amenities = detection_results.get("amenities", {})
        floor_elements = detection_results.get("floor_elements", {})

        # 1. Solar Score (max 20 pts)
        solar_area = amenities.get("total_solar_area", 0.0)
        solar_score = min(20.0, round((solar_area / max(1.0, building_area * 0.10)) * 20.0, 2))

        # 2. Water / RWH Score (max 20 pts)
        rwh_count = amenities.get("rwh_pit_count", 0)
        water_score = 20.0 if rwh_count >= 1 else 0.0

        # 3. Landscape / Green Coverage Score (max 20 pts)
        landscape_area = floor_elements.get("total_landscape_area", 0.0)
        landscape_pct = (landscape_area / plot_area * 100.0) if plot_area > 0 else 0.0
        landscape_score = min(20.0, round((landscape_pct / 15.0) * 20.0, 2))

        # 4. Waste / STP Score (max 20 pts)
        stp_count = amenities.get("stp_count", 0)
        waste_score = 20.0 if stp_count >= 1 else 10.0

        # 5. Energy Efficiency Score (max 20 pts)
        energy_score = 15.0  # Base standard building envelope compliance

        total_green_score = round(solar_score + water_score + landscape_score + waste_score + energy_score, 2)
        compliance_pct = total_green_score

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
        if rwh_count < 1:
            recommendations.append("Provide Rain Water Harvesting recharge pits to gain mandatory water conservation points.")
        if landscape_pct < 15.0:
            recommendations.append(f"Increase green landscape softscape area from {round(landscape_pct, 1)}% to minimum 15%.")

        return {
            "standard_evaluated": standard.upper(),
            "overall_green_score": total_green_score,
            "compliance_percentage": compliance_pct,
            "green_rating": rating,
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
