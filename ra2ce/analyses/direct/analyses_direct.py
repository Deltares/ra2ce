"""
                    GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

    Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023 Stichting Deltares

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import logging
import time
from pathlib import Path
from typing import Any

import geopandas as gpd

from ra2ce.analyses.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionDirect,
)
from ra2ce.analyses.analysis_config_data.enums.analysis_direct_enum import (
    AnalysisDirectEnum,
)
from ra2ce.analyses.direct.cost_benefit_analysis import EffectivenessMeasures
from ra2ce.analyses.direct.damage.manual_damage_functions import ManualDamageFunctions
from ra2ce.analyses.direct.damage_calculation import (
    DamageNetworkEvents,
    DamageNetworkReturnPeriods,
)
from ra2ce.graph.graph_files.graph_files_collection import GraphFilesCollection


class DirectAnalyses:  ### THIS SHOULD ONLY DO COORDINATION
    """
    Coordination class for all direct damage analysis

    Methods of this class are independent modules to do:
     - direct damage analysis
     - cost-benefit / cost-effectiveness calculations

    """

    config: AnalysisConfigData
    graph_files: GraphFilesCollection

    def __init__(self, config: AnalysisConfigData, graph_files: GraphFilesCollection):
        self.config = config
        self.graph_files = graph_files

    def execute(self):
        """Main Coordinator of all direct damage analysis

        This function uses the analyses.ini file to make a decision between:
         - running the direct damage calculations module
         - running the cost-benefit analysis module (effectiveness_measures)

        """

        for analysis in self.config.direct:
            logging.info(
                f"----------------------------- Started analyzing '{analysis.name}'  -----------------------------"
            )
            starttime = time.time()

            if analysis.analysis == AnalysisDirectEnum.DIRECT:
                gdf = self.road_damage(
                    analysis
                )  # calls the coordinator for road damage calculation

            elif analysis.analysis == AnalysisDirectEnum.EFFECTIVENESS_MEASURES:
                gdf = self.effectiveness_measures(analysis)

            else:
                gdf = []

            _output_path = self.config.output_path.joinpath(
                analysis.analysis.config_value
            )
            if analysis.save_gpkg:
                gpkg_path = _output_path.joinpath(
                    analysis.name.replace(" ", "_") + ".gpkg"
                )
                save_gdf(gdf, gpkg_path, "GPKG")
            if analysis.save_csv:
                csv_path = _output_path.joinpath(
                    analysis.name.replace(" ", "_") + ".csv"
                )
                del gdf["geometry"]
                gdf.to_csv(csv_path, index=False)

            endtime = time.time()
            logging.info(
                f"----------------------------- Analysis '{analysis.name}' finished. "
                f"Time: {str(round(endtime - starttime, 2))}s  -----------------------------"
            )

    def road_damage(self, analysis: AnalysisSectionDirect) -> gpd.GeoDataFrame:
        """
        ### CONTROLLER FOR CALCULATING THE ROAD DAMAGE

        Arguments:
            *analysis* (AnalysisSectionDirect) : contains part of the settings from the analysis ini

        Returns:
            *result_gdf* (GeoDataFrame) : The original hazard dataframe with the result of the damage calculations added

        """
        # Open the network with hazard data
        road_gdf = self.graph_files.base_network_hazard.get_graph()
        road_gdf.columns = rename_road_gdf_to_conventions(road_gdf.columns)

        # Find the hazard columns; these may be events or return periods
        val_cols = [
            col for col in road_gdf.columns if (col[0].isupper() and col[1] == "_")
        ]

        # Read the desired damage function
        damage_function = analysis.damage_curve

        # If you want to use manual damage functions, these need to be loaded first
        manual_damage_functions = None
        if analysis.damage_curve == "MAN":
            manual_damage_functions = ManualDamageFunctions()
            manual_damage_functions.find_damage_functions(
                folder=(self.config.input_path.joinpath("damage_functions"))
            )
            manual_damage_functions.load_damage_functions()

        # Choose between event or return period based analysis
        if analysis.event_type == "event":
            event_gdf = DamageNetworkEvents(road_gdf, val_cols)
            event_gdf.main(
                damage_function=damage_function,
                manual_damage_functions=manual_damage_functions,
            )

            return event_gdf.gdf

        elif analysis.event_type == "return_period":
            return_period_gdf = DamageNetworkReturnPeriods(road_gdf, val_cols)
            return_period_gdf.main(
                damage_function=damage_function,
                manual_damage_functions=manual_damage_functions,
            )

            if analysis.risk_calculation:  # Check if risk_calculation is demanded
                if analysis.risk_calculation != "none":
                    return_period_gdf.control_risk_calculation(
                        mode=analysis.risk_calculation
                    )

            else:
                logging.info(
                    """No parameters for risk calculation are specified. 
                             Add key [risk_calculation] to analyses.ini."""
                )

            return return_period_gdf.gdf

        raise ValueError(
            "The hazard calculation does not know what to do if the analysis specifies {}".format(
                analysis.event_type
            )
        )

    def effectiveness_measures(self, analysis: AnalysisSectionDirect):
        """This function calculated the efficiency of measures. Input is a csv file with efficiency
        and a list of different aspects you want to check.
        """
        em = EffectivenessMeasures(self.config, analysis)
        effectiveness_dict = em.load_effectiveness_table()

        gdf_in = self.graph_files.base_network_hazard.get_graph()

        if analysis.create_table is True:
            df = em.create_feature_table(
                self.config.input_path.joinpath("direct", analysis.file_name)
            )
        else:
            df = em.load_table(
                self.config.input_path.joinpath("direct"),
                analysis.file_name.replace(".gpkg", ".csv"),
            )

        df = em.calculate_strategy_effectiveness(df, effectiveness_dict)
        df = em.knmi_correction(df)
        df_cba, costs_dict = em.cost_benefit_analysis(effectiveness_dict)
        df_cba.round(2).to_csv(
            self.config.output_path.joinpath(
                analysis.analysis.config_value, "cost_benefit_analysis.csv"
            ),
            decimal=",",
            sep=";",
            index=False,
            float_format="%.2f",
        )
        df = em.calculate_cost_reduction(df, effectiveness_dict)
        df_costs = em.calculate_strategy_costs(df, costs_dict)
        df_costs = df_costs.astype(float).round(2)
        df_costs.to_csv(
            self.config.output_path.joinpath(
                analysis.analysis.config_value, "output_analysis.csv"
            ),
            decimal=",",
            sep=";",
            index=False,
            float_format="%.2f",
        )
        gdf = gdf_in.merge(df, how="left", on="LinkNr")
        return gdf


def save_gdf(gdf: gpd.GeoDataFrame, save_path: Path, driver: str):
    """Takes in a geodataframe object and outputs shapefiles at the paths indicated by edge_shp and node_shp

    Arguments:
        gdf [geodataframe]: geodataframe object to be converted
        save_path [Path]: path to save
        driver [str]: defines the file format
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
    gdf.to_file(save_path, driver=driver)
    logging.info("Results saved to: {}".format(save_path))


def rename_road_gdf_to_conventions(road_gdf_columns: Any) -> Any:
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
