import logging
from pathlib import Path

from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionDamages,
)
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.damages.analysis_damages_protocol import AnalysisDamagesProtocol
from ra2ce.analysis.damages.damage.manual_damage_functions import ManualDamageFunctions
from ra2ce.analysis.damages.damage_calculation import (
    DamageNetworkEvents,
    DamageNetworkReturnPeriods,
)
from ra2ce.network.graph_files.network_file import NetworkFile


class Damages(AnalysisDamagesProtocol):
    analysis: AnalysisSectionDamages
    graph_file: NetworkFile
    graph_file_hazard: NetworkFile
    input_path: Path
    output_path: Path

    def __init__(
        self,
        analysis_input: AnalysisInputWrapper,
    ) -> None:
        self.analysis = analysis_input.analysis
        self.graph_file = None
        self.graph_file_hazard = analysis_input.graph_file_hazard
        self.input_path = analysis_input.input_path
        self.output_path = analysis_input.output_path

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
                    new_cols.append(f"{hazard_prefix}_" + c)
                else:
                    new_cols.append(c)

            ### Todo add handling of events if this gives a problem
            return new_cols

        hazard_prefix = "F"
        # Open the network with hazard data
        road_gdf = self.graph_file_hazard.get_graph()
        road_gdf.columns = _rename_road_gdf_to_conventions(road_gdf.columns)

        # Find the hazard columns; these may be events or return periods
        val_cols = [
            col for col in road_gdf.columns if f"{hazard_prefix}" in col.split("_")
        ]

        # Read the desired damage function
        damage_function = self.analysis.damage_curve

        # If you want to use manual damage functions, these need to be loaded first
        manual_damage_functions = None
        if self.analysis.damage_curve == DamageCurveEnum.MAN:
            manual_damage_functions = ManualDamageFunctions()
            manual_damage_functions.find_damage_functions(
                folder=(self.input_path.joinpath("damage_functions"))
            )
            manual_damage_functions.load_damage_functions()

        # Choose between event or return period based analysis
        if self.analysis.event_type == EventTypeEnum.EVENT:
            event_gdf = DamageNetworkEvents(
                road_gdf, val_cols, self.analysis.representative_damage_percentage
            )
            event_gdf.main(
                damage_function=damage_function,
                manual_damage_functions=manual_damage_functions,
            )

            return event_gdf.gdf

        elif self.analysis.event_type == EventTypeEnum.RETURN_PERIOD:
            return_period_gdf = DamageNetworkReturnPeriods(
                road_gdf, val_cols, self.analysis.representative_damage_percentage
            )
            return_period_gdf.main(
                damage_function=damage_function,
                manual_damage_functions=manual_damage_functions,
            )

            if (
                self.analysis.risk_calculation_mode != RiskCalculationModeEnum.INVALID
            ):  # Check if risk_calculation is demanded
                if self.analysis.risk_calculation_mode != RiskCalculationModeEnum.NONE:
                    return_period_gdf.control_risk_calculation(
                        mode=self.analysis.risk_calculation_mode,
                        year=self.analysis.risk_calculation_year,
                    )

            else:
                logging.info(
                    """No parameters for risk calculation are specified. 
                             Add key [risk_calculation_mode] to analyses.ini."""
                )

            return return_period_gdf.gdf

        raise ValueError(
            "The hazard calculation does not know what to do if the analysis specifies {}".format(
                self.analysis.event_type
            )
        )
