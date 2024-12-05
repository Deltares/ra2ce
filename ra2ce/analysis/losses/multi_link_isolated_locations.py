import copy
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from geopandas import GeoDataFrame, overlay, read_feather
from pyproj import CRS

from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames
from ra2ce.network.networks_utils import buffer_geometry, graph_to_gdf


class MultiLinkIsolatedLocations(AnalysisBase, AnalysisLossesProtocol):
    analysis: AnalysisSectionLosses
    graph_file_hazard: GraphFile
    input_path: Path
    static_path: Path
    output_path: Path
    hazard_names: HazardNames

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

    def utm_crs(self, bbox: list[float]) -> CRS:
        """Returns wkt string of nearest UTM projects
        Parameters
        ----------
        bbox : array-like of floats
            (xmin, ymin, xmax, ymax) bounding box in latlon WGS84 (EPSG:4326) coordinates
        Returns
        -------
        crs: pyproj.CRS
            CRS of UTM projection

        FROM HYDROMT: https://github.com/Deltares/hydromt - 10.5281/zenodo.6107669
        """
        left, bottom, right, top = bbox
        x = (left + right) / 2
        y = (top + bottom) / 2
        kwargs = dict(zone=int(np.ceil((x + 180) / 6)))
        # BUGFIX hydroMT v0.3.5: south=False doesn't work only add south=True if y<0
        if y < 0:
            kwargs.update(south=True)
        # BUGFIX hydroMT v0.4.6: add datum
        epsg = CRS(proj="utm", datum="WGS84", ellps="WGS84", **kwargs).to_epsg()
        return CRS.from_epsg(epsg)

    def remove_edges_from_largest_component(self, disconnected_graph: nx.Graph) -> None:
        """
        This function removes all edges from the largest connected component of a graph.

        Args:
            disconnected_graph (nx.Graph): The graph from which to remove the edges.
        """
        connected_components = list(
            c for c in nx.connected_components(disconnected_graph)
        )
        connected_components_size = list(
            len(c) for c in nx.connected_components(disconnected_graph)
        )

        largest_comp_index = connected_components_size.index(
            max(connected_components_size)
        )
        edges_from_lagest_component = list(
            disconnected_graph.subgraph(
                connected_components[largest_comp_index]
            ).edges()
        )
        disconnected_graph.remove_edges_from(edges_from_lagest_component)

    def get_network_with_edge_fid(self, graph: nx.Graph) -> GeoDataFrame:
        """
        This function converts a NetworkX graph into a GeoDataFrame representing the network.
        It also constructs an 'edge_fid' column based on the 'node_A' and 'node_B' columns, following a specific convention.

        Args:
            G (nx.Graph): The NetworkX graph to be converted.

        Returns:
            gpd.GeoDataFrame: The resulting GeoDataFrame, with an added 'edge_fid' column.
        """
        network = graph_to_gdf(graph)[0]
        # TODO: add making "edges_fid" (internal convention) to graph_to_gdf
        if all(c_idx in network.index.names for c_idx in ["u", "v"]):
            network["edge_fid"] = [f"{na}_{nb}" for (na, nb, _) in network.index]
        elif all(c_idx in network.columns for c_idx in ["node_A", "node_B"]):
            # shapefiles
            network["edge_fid"] = [
                f"{na}_{nb}" for na, nb in network["node_A", "node_B"].values
            ]
        return network[["edge_fid", "geometry"]]

    def _summarize_locations(
        self, locations: GeoDataFrame, cat_col: str, hazard_id: str
    ) -> pd.DataFrame:
        """
        This function summarizes the hazard impacts on different categories of locations.
        It adds a counter for each hazard type and aggregates the data per category.

        Args:
            locations (gpd.GeoDataFrame): A GeoDataFrame containing the locations and their hazard impacts.
            cat_col (str): The column name in the locations GeoDataFrame that represents the location categories.
            hazard_id (str): The identifier for the hazard being considered.

        Returns:
            pd.DataFrame: A DataFrame summarizing the number of isolated locations per category for the given hazard.
        """
        # add counter
        locations[f"i_{hazard_id}"] = 1  # add counter
        # make an overview of the locations, aggregated per category
        df_aggregation = (
            locations.groupby(by=[cat_col, f"i_type_{hazard_id}"])[f"i_{hazard_id}"]
            .sum()
            .reset_index()
        )
        df_aggregation["hazard"] = hazard_id
        df_aggregation.rename(columns={f"i_{hazard_id}": "nr_isolated"}, inplace=True)
        return df_aggregation

    def multi_link_isolated_locations(
        self, graph: nx.Graph, analysis: AnalysisSectionLosses, crs=4326
    ) -> tuple[GeoDataFrame, pd.DataFrame]:
        """
        This function identifies locations that are flooded or isolated due to the disruption of the network caused by a hazard.
        It iterates over multiple hazard scenarios, modifies the graph to represent direct and indirect impacts, and then
        spatially joins the impacted network with the location data to find out which locations are affected.

        Args:
            graph (nx.Graph): The original graph representing the network, with additional hazard information.
            analysis (AnalysisSectionLosses): The configuration of the analysis, which contains the threshold for considering a hazard impact significant.
            crs (int, optional): The coordinate reference system used for geographical data. Defaults to 4326 (WGS84).

        Returns:
            tuple (gpd.GeoDataFrame, pd.DataFrame): A tuple containing the location GeoDataFrame updated with hazard impacts,
                and a DataFrame summarizing the impacts per location category.
        """

        def _is_not_none(value):
            return (
                value is not None
                and value is not pd.NA
                and not pd.isna(value)
                and not np.isnan(value)
            )

        # Load the point shapefile with the locations of which the isolated locations should be identified.
        locations = read_feather(
            self.static_path.joinpath("output_graph", "locations_hazard.feather")
        )
        # TODO PUT CRS IN DOCUMENTATION OR MAKE CHANGABLE
        # reproject the datasets to be able to make a buffer in meters
        nearest_utm = self.utm_crs(locations.total_bounds)

        # create an empty list to append the df_aggregation to
        aggregation = pd.DataFrame()
        for hazard in self.hazard_names.names:
            # for each hazard event
            hazard_name = self.hazard_names.get_name(hazard)

            graph_hz_direct = copy.deepcopy(graph)
            graph_hz_indirect = copy.deepcopy(graph)

            # filter graph edges that are directly disrupted by the hazard(s), i.e. flooded
            edges = [e for e in graph.edges.data(keys=True) if hazard_name in e[-1]]
            edges_hz_direct = [
                e
                for e in edges
                if (hazard_name in e[-1])
                and (
                    _is_not_none(e[-1][hazard_name])
                    and (e[-1][hazard_name] > float(analysis.threshold))
                    & (
                        ("bridge" not in e[-1])
                        or ("bridge" in e[-1] and e[-1]["bridge"] != "yes")
                    )
                )
            ]
            edges_hz_indirect = [e for e in edges if e not in edges_hz_direct]

            # get indirect graph - remove the edges that are impacted by hazard directly
            graph_hz_indirect.remove_edges_from(edges_hz_direct)
            # get indirect graph without the largest component, i.e. isolated graph
            self.remove_edges_from_largest_component(graph_hz_indirect)

            # get direct graph - romove the edges that are impacted by hazard indirectly
            graph_hz_direct.remove_edges_from(edges_hz_indirect)

            # get isolated network
            network_hz_indirect = GeoDataFrame()
            if len(graph_hz_indirect.edges) > 0:
                network_hz_indirect = self.get_network_with_edge_fid(graph_hz_indirect)
                network_hz_indirect[f"i_type_{hazard_name[:-3]}"] = "isolated"
                # reproject the datasets to be able to make a buffer in meters
                network_hz_indirect = network_hz_indirect.set_crs(
                    crs=crs, allow_override=True
                )
                network_hz_indirect.to_crs(crs=nearest_utm, inplace=True)

            # get flooded network
            network_hz_direct = GeoDataFrame()
            if len(graph_hz_direct.edges) > 0:
                network_hz_direct = self.get_network_with_edge_fid(graph_hz_direct)
                network_hz_direct[f"i_type_{hazard_name[:-3]}"] = "flooded"
                # reproject the datasets to be able to make a buffer in meters
                network_hz_direct = network_hz_direct.set_crs(
                    crs=crs, allow_override=True
                )
                network_hz_direct.to_crs(crs=nearest_utm, inplace=True)

            # get hazard roads
            # merge buffer and set original crs
            results_hz_roads = GeoDataFrame(
                pd.concat([network_hz_direct, network_hz_indirect])
            )
            results_hz_roads = buffer_geometry(
                results_hz_roads, analysis.buffer_meters
            ).to_crs(crs=crs)
            # Save the output
            results_hz_roads.to_file(
                self.output_path.joinpath(
                    analysis.analysis.config_value,
                    f"flooded_and_isolated_roads_{hazard_name}.gpkg",
                )
            )

            # relate the locations to network disruption due to hazard by spatial overlay
            results_hz_roads.reset_index(inplace=True)
            locations_hz = overlay(
                locations, results_hz_roads, how="intersection", keep_geom_type=True
            )

            # Replace nan with 0 for the water depth columns
            # TODO: this should always be done in hazard class
            locations_hz[hazard_name] = locations_hz[hazard_name].fillna(0)

            # TODO: Put in analyses.ini file a variable to set the threshold for locations that are not isolated when they are flooded.
            # Extract the flood depth of the locations
            # intersect = intersect.loc[intersect[hazard_name] > analysis.threshold_locations]

            # get location stats
            df_aggregation = self._summarize_locations(
                locations_hz,
                cat_col=analysis.category_field_name,
                hazard_id=hazard_name[:-3],
            )

            # add to exisiting results
            aggregation = pd.concat([aggregation, df_aggregation], axis=0)

        # Set the locations_hz geopandas dataframe back to the original crs
        locations_hz.to_crs(crs=crs, inplace=True)

        return locations_hz, aggregation

    def execute(self) -> AnalysisResultWrapper:
        _output_path = self.output_path.joinpath(self.analysis.analysis.config_value)

        (gdf, df) = self.multi_link_isolated_locations(
            self.graph_file_hazard.get_graph(), self.analysis
        )

        df_path = _output_path.joinpath(
            self.analysis.name.replace(" ", "_") + "_results.csv"
        )
        df.to_csv(df_path, index=False)

        return self.generate_result_wrapper(gdf)
