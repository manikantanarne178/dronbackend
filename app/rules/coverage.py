from app.services.area_service import AreaService


class CoverageRule:

    @staticmethod
    def check(plot, building, config):

        if plot is None:
            return {
                "rule": "Ground Coverage",
                "status": "FAIL",
                "reason": "Plot not detected"
            }

        if building is None:
            return {
                "rule": "Ground Coverage",
                "status": "FAIL",
                "reason": "Building not detected"
            }

        coverage = AreaService.ground_coverage(
            plot,
            building
        )

        max_coverage = float(
            config.get_value(
                "coverage",
                "max_coverage"
            )
        )

        return {
            "rule": "Ground Coverage",
            "required": f"<= {max_coverage}%",
            "actual": round(coverage, 2),
            "status": "PASS" if coverage <= max_coverage else "FAIL"
        }