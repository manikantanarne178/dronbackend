class PlotRule:

    MINIMUM_AREA = 150.0

    @staticmethod
    def check(plot):

        if plot is None:
            return {
                "rule": "Plot Area",
                "status": "FAIL",
                "reason": "Plot not detected"
            }

        area = plot["area"]

        return {
            "rule": "Plot Area",
            "required": PlotRule.MINIMUM_AREA,
            "actual": round(area, 2),
            "status": "PASS" if area >= PlotRule.MINIMUM_AREA else "FAIL"
        }