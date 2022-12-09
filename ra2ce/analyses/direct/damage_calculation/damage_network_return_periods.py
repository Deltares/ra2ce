from ra2ce.analyses.direct.damage_calculation.damage_network_base import (
    DamageNetworkBase,
)


class DamageNetworkReturnPeriods(DamageNetworkBase):
    """A road network gdf with Return-Period based hazard data stored in it, and for which damages can be calculated
    @Author: Kees van Ginkel

    Mandatory attributes:
        *self.rps* (set)  : all available unique events
        *self.stats* (set)   : the available statistics
    """

    def __init__(self, road_gdf, val_cols):
        # Construct using the parent class __init__
        super().__init__(road_gdf, val_cols)

        self.return_periods = set(
            [x.split("_")[1] for x in val_cols]
        )  # set of unique return_periods

        if not len(self.return_periods) > 1:
            raise ValueError("No return_period cols present in hazard data")

    ### Controlers for EAD calculation
    def main(self, damage_function, manual_damage_functions):

        assert len(self.return_periods) > 0, "no return periods identified"
        assert "me" in self.stats, "mean water depth (key: me) is missing"
        assert "fr" in self.stats, "inundated fraction (key: fr) is missing"

        self.do_cleanup_and_mask_creation()

        if damage_function == "HZ":
            self.calculate_damage_HZ(events=self.return_periods)

        if damage_function == "OSD":
            self.calculate_damage_OSdaMage(events=self.return_periods)

        if damage_function == "MAN":
            self.calculate_damage_manual_functions(
                events=self.events, manual_damage_functions=manual_damage_functions
            )
