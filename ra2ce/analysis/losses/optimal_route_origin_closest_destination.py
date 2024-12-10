import logging
from pathlib import Path

from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.analysis_result.analysis_result import AnalysisResult
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol
from ra2ce.analysis.losses.origin_closest_destination import OriginClosestDestination
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames
from ra2ce.network.network_config_data.network_config_data import (
    OriginsDestinationsSection,
)
from ra2ce.network.networks_utils import graph_to_gpkg


class OptimalRouteOriginClosestDestination(AnalysisBase, AnalysisLossesProtocol):
    analysis: AnalysisSectionLosses
    graph_file_hazard: GraphFile
    input_path: Path
    static_path: Path
    output_path: Path
    hazard_names: HazardNames
    origins_destinations: OriginsDestinationsSection
    file_id: str
    _analysis_input: AnalysisInputWrapper

    def __init__(
        self,
        analysis_input: AnalysisInputWrapper,
    ) -> None:
        self.analysis = analysis_input.analysis
        self.graph_file_hazard = analysis_input.graph_file_hazard
        self.input_path = analysis_input.input_path
        self.static_path = analysis_input.static_path
        self.output_path = analysis_input.output_path
        self.hazard_names = analysis_input.hazard_names
        self.origins_destinations = analysis_input.origins_destinations
        self.file_id = analysis_input.file_id
        self._analysis_input = analysis_input

    def execute(self) -> AnalysisResultWrapper:
        analyzer = OriginClosestDestination(self._analysis_input)
        (
            _,
            opt_routes,
            destinations,
        ) = analyzer.optimal_route_origin_closest_destination()

        # TODO: This does not seem correct, why were we returning None?
        def get_analysis_result(
            gdf_result: GeoDataFrame, suffix_name: str
        ) -> AnalysisResult:
            _ar = AnalysisResult(
                analysis_result=gdf_result,
                analysis_config=self.analysis,
                output_path=self.output_path,
            )
            _ar.analysis_name = self.analysis.name.replace(" ", "_") + suffix_name
            return _ar

        return AnalysisResultWrapper(
            results_collection=[
                # CSV
                get_analysis_result(destinations, "_destinations"),
                get_analysis_result(opt_routes, "_optimal_routes"),
            ]
        )
