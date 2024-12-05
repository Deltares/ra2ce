from pathlib import Path

from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol
from ra2ce.analysis.losses.origin_closest_destination import OriginClosestDestination
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames
from ra2ce.network.network_config_data.network_config_data import (
    OriginsDestinationsSection,
)
from ra2ce.network.networks_utils import graph_to_gpkg
from ra2ce.ra2ce_logger import logging


class MultiLinkOriginClosestDestination(AnalysisBase, AnalysisLossesProtocol):
    analysis: AnalysisSectionLosses
    graph_file: GraphFile
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
        self.graph_file = analysis_input.graph_file
        self.graph_file_hazard = analysis_input.graph_file_hazard
        self.input_path = analysis_input.input_path
        self.static_path = analysis_input.static_path
        self.output_path = analysis_input.output_path
        self.hazard_names = analysis_input.hazard_names
        self.origins_destinations = analysis_input.origins_destinations
        self.file_id = analysis_input.file_id
        self._analysis_input = analysis_input

    def _save_gdf(self, gdf: GeoDataFrame, save_path: Path) -> None:
        """Takes in a geodataframe object and outputs shapefiles at the paths indicated by edge_shp and node_shp

        Arguments:
            gdf [geodataframe]: geodataframe object to be converted
            save_path [str]: output path including extension for edges shapefile
        Returns:
            None
        """
        # save to shapefile
        gdf.crs = "epsg:4326"  # TODO: decide if this should be variable with e.g. an output_crs configured

        for col in gdf.columns:
            if gdf[col].dtype == object and col != gdf.geometry.name:
                gdf[col] = gdf[col].astype(str)

        if save_path.exists():
            save_path.unlink()
        gdf.to_file(save_path, driver="GPKG")
        logging.info("Results saved to: {}".format(save_path))

    def execute(self) -> AnalysisResultWrapper:
        def _save_gpkg_analysis(
            base_graph,
            to_save_gdf: list[GeoDataFrame],
            to_save_gdf_names: list[str],
        ):
            for to_save, save_name in zip(to_save_gdf, to_save_gdf_names):
                if not to_save.empty:
                    gpkg_path = _output_path.joinpath(
                        self.analysis.name.replace(" ", "_") + f"_{save_name}.gpkg"
                    )
                    self._save_gdf(to_save, gpkg_path)

            # Save the Graph
            gpkg_path_nodes = _output_path.joinpath(
                self.analysis.name.replace(" ", "_") + "_results_nodes.gpkg"
            )
            gpkg_path_edges = _output_path.joinpath(
                self.analysis.name.replace(" ", "_") + "_results_edges.gpkg"
            )
            graph_to_gpkg(base_graph, gpkg_path_edges, gpkg_path_nodes)

        _output_path = self.output_path.joinpath(self.analysis.analysis.config_value)

        analyzer = OriginClosestDestination(self._analysis_input)

        if self.analysis.calculate_route_without_disruption:
            (
                base_graph,
                opt_routes_without_hazard,
                destinations,
            ) = analyzer.optimal_route_origin_closest_destination()

            if self.graph_file_hazard.file is None:
                origins = analyzer.load_origins()
                opt_routes_with_hazard = GeoDataFrame(data=None)
            else:
                (
                    base_graph,
                    origins,
                    destinations,
                    agg_results,
                    opt_routes_with_hazard,
                ) = analyzer.multi_link_origin_closest_destination()

                (
                    opt_routes_with_hazard
                ) = analyzer.difference_length_with_without_hazard(
                    opt_routes_with_hazard, opt_routes_without_hazard
                )
        else:
            (
                base_graph,
                origins,
                destinations,
                agg_results,
                opt_routes_with_hazard,
            ) = analyzer.multi_link_origin_closest_destination()
            opt_routes_without_hazard = GeoDataFrame()

        if self.analysis.save_gpkg:
            # Save the GeoDataFrames
            to_save_gdf = [
                origins,
                destinations,
                opt_routes_without_hazard,
                opt_routes_with_hazard,
            ]
            to_save_gdf_names = [
                "origins",
                "destinations",
                "optimal_routes_without_hazard",
                "optimal_routes_with_hazard",
            ]
            _save_gpkg_analysis(base_graph, to_save_gdf, to_save_gdf_names)
        if self.analysis.save_csv:
            csv_path = _output_path.joinpath(
                self.analysis.name.replace(" ", "_") + "_destinations.csv"
            )
            if "geometry" in destinations.columns:
                del destinations["geometry"]
            if not csv_path.parent.exists():
                csv_path.parent.mkdir(parents=True)
            destinations.to_csv(csv_path, index=False)

            csv_path = _output_path.joinpath(
                self.analysis.name.replace(" ", "_") + "_optimal_routes.csv"
            )
            if not opt_routes_without_hazard.empty:
                del opt_routes_without_hazard["geometry"]
                opt_routes_without_hazard.to_csv(csv_path, index=False)
            if not opt_routes_with_hazard.empty:
                del opt_routes_with_hazard["geometry"]
                opt_routes_with_hazard.to_csv(csv_path, index=False)

        if self.graph_file_hazard.file is not None:
            agg_results.to_excel(
                _output_path.joinpath(
                    self.analysis.name.replace(" ", "_") + "_results.xlsx"
                ),
                index=False,
            )

        # TODO: This does not seem correct, why were we returning None?
        return self.generate_result_wrapper(analysis_result=None)
