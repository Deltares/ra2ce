from __future__ import annotations

from pathlib import Path

from ra2ce.analyses.direct.damage_calculation.damage_network_base import (
    DamageNetworkBase,
)


class DamageNetworkEvents(DamageNetworkBase):
    """A road network gdf with EVENT-BASED hazard data stored in it, and for which damages can be calculated

    @Author: Kees van Ginkel

    Mandatory attributes:
        *self.events* (set)  : all available unique events
        *self.stats* (set)   : the available statistics
    """

    def __init__(self, road_gdf, val_cols):
        # Construct using the parent class __init__
        super().__init__(road_gdf, val_cols)
        self.events = set([x.split("_")[1] for x in val_cols])  # set of unique events

        if not any(self.events):
            raise ValueError("No event cols present in hazard data")

    ### Controler for Event-based damage calculation
    def main(self, damage_function, manual_damage_functions=None):
        assert len(self.events) > 0, "no return periods identified"
        assert "me" in self.stats, "mean water depth (key: me) is missing"
        assert "fr" in self.stats, "inundated fraction (key: fr) is missing"

        self.do_cleanup_and_mask_creation()

        if damage_function == "HZ":
            self.calculate_damage_HZ(events=self.events)

        if damage_function == "OSD":
            self.calculate_damage_OSdaMage(events=self.events)

        if damage_function == "MAN":
            self.calculate_damage_manual_functions(
                events=self.events, manual_damage_functions=manual_damage_functions
            )


# class DamageNetworkEventsBuilder:
#     @staticmethod
#     def from_csv_file(file_path) -> DamageNetworkEvents:
#         pass
#
#     @staticmethod
#     def from_pandas(pd_dataframe) -> DamageNetworkEvents:
#         pass
