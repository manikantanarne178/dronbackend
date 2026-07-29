class AreaService:

    @staticmethod
    def plot_area(plot):

        if plot is None:
            return 0.0

        return float(plot.get("area", 0.0))

    @staticmethod
    def building_area(building):

        if building is None:
            return 0.0

        return float(building.get("area", 0.0))

    @staticmethod
    def total_floor_area(building):

        if building is None:
            return 0.0

        # Single-floor assumption for now
        return float(building.get("area", 0.0))

    @staticmethod
    def ground_coverage(plot, building):

        plot_area = AreaService.plot_area(plot)
        building_area = AreaService.building_area(building)

        if plot_area <= 0:
            return 0.0

        return (building_area / plot_area) * 100