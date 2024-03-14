import logging
from pathlib import Path

from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionDirect,
)
from ra2ce.analysis.direct.analysis_direct_protocol import AnalysisDirectProtocol
from ra2ce.analysis.direct.damage.manual_damage_functions import ManualDamageFunctions
from ra2ce.analysis.direct.damage_calculation import (
    DamageNetworkEvents,
    DamageNetworkReturnPeriods,
)
from ra2ce.network.graph_files.network_file import NetworkFile


class DirectDamage(AnalysisDirectProtocol):
    graph_file: NetworkFile
    analysis: AnalysisSectionDirect
    input_path: Path
    output_path: Path
    result: GeoDataFrame

    def __init__(
        self,
        graph_file: NetworkFile,
        analysis: AnalysisSectionDirect,
        input_path: Path,
        output_path: Path,
    ) -> None:
        self.graph_file = graph_file
        self.analysis = analysis
        self.input_path = input_path
        self.output_path = output_path
        self.result = None

    def execute(self) -> GeoDataFrame:

        def _rename_road_gdf_to_conventions(road_gdf_columns: list[str]) -> list[str]:
            """
            Rename the columns in the road_gdf to the conventions of the ra2ce documentation

            'eg' RP100_fr -> F_RP100_me
                        -> F_EV1_mi

            """
            cs = road_gdf_columns
            ### Handle return period columns
            new_cols = []
            for c in cs:
                if c.startswith("RP") or c.startswith("EV"):
                    new_cols.append("F_" + c)
                else:
                    new_cols.append(c)

            ### Todo add handling of events if this gives a problem
            return new_cols

        # Open the network with hazard data
        road_gdf = self.graph_file.get_graph()
        road_gdf.columns = _rename_road_gdf_to_conventions(road_gdf.columns)

        # Find the hazard columns; these may be events or return periods
        val_cols = [
            col for col in road_gdf.columns if (col[0].isupper() and col[1] == "_")
        ]

        # Read the desired damage function
        damage_function = self.analysis.damage_curve

        # If you want to use manual damage functions, these need to be loaded first
        manual_damage_functions = None
        if self.analysis.damage_curve == "MAN":
            manual_damage_functions = ManualDamageFunctions()
            manual_damage_functions.find_damage_functions(
                folder=(self.input_path.joinpath("damage_functions"))
            )
            manual_damage_functions.load_damage_functions()

        # Choose between event or return period based analysis
        if self.analysis.event_type == "event":
            event_gdf = DamageNetworkEvents(road_gdf, val_cols)
            event_gdf.main(
                damage_function=damage_function,
                manual_damage_functions=manual_damage_functions,
            )

            return event_gdf.gdf

        elif self.analysis.event_type == "return_period":
            return_period_gdf = DamageNetworkReturnPeriods(road_gdf, val_cols)
            return_period_gdf.main(
                damage_function=damage_function,
                manual_damage_functions=manual_damage_functions,
            )

            if self.analysis.risk_calculation:  # Check if risk_calculation is demanded
                if self.analysis.risk_calculation != "none":
                    return_period_gdf.control_risk_calculation(
                        mode=self.analysis.risk_calculation
                    )

            else:
                logging.info(
                    """No parameters for risk calculation are specified. 
                             Add key [risk_calculation] to analyses.ini."""
                )

            return return_period_gdf.gdf

        raise ValueError(
            "The hazard calculation does not know what to do if the analysis specifies {}".format(
                self.analysis.event_type
            )
        )
