from app.services.area_service import AreaService


class FSIRule:

    @staticmethod
    def check(plot, building, config):

        if plot is None:
            return {
                "rule": "FSI",
                "status": "FAIL",
                "reason": "Plot not detected"
            }

        if building is None:
            return {
                "rule": "FSI",
                "status": "FAIL",
                "reason": "Building not detected"
            }

        plot_area = AreaService.plot_area(plot)
        building_area = AreaService.total_floor_area(building)

        if plot_area <= 0:
            return {
                "rule": "FSI",
                "status": "FAIL",
                "reason": "Invalid plot area"
            }

        max_fsi = float(
            config.get_value(
                "fsi",
                "max_fsi"
            )
        )

        actual_fsi = building_area / plot_area

        return {
            "rule": "FSI",
            "required": f"<= {max_fsi}",
            "actual": round(actual_fsi, 2),
            "status": "PASS" if actual_fsi <= max_fsi else "FAIL"
        }