import logging
import time
from pathlib import Path

import geopandas as gpd

from ra2ce.analyses.direct.cost_benefit_analysis import EffectivenessMeasures
from ra2ce.analyses.direct.damage.damage_fraction_uniform import DamageFractionUniform
from ra2ce.analyses.direct.damage.manual_damage_functions import ManualDamageFunctions
from ra2ce.analyses.direct.damage.max_damage import MaxDamageByRoadTypeByLane
from ra2ce.analyses.direct.damage_calculation import (
    DamageNetworkEvents,
    DamageNetworkReturnPeriods,
)


class DirectAnalyses:  ### THIS SHOULD ONLY DO COORDINATION
    """
    Coordination classs for all direct damage analysis

    Methods of this class are independent modules to do:
     - direct damage analysis
     - cost-benefit / cost-effectiveness calculations

    """

    def __init__(self, config, graphs):
        self.config = config
        self.graphs = graphs

    def execute(self):
        """Main Coordinator of all direct damage analysis

        This function uses the analyses.ini file to make a decision between:
         - running the direct damage calculations module
         - running the cost-benefit analysis module (effectiveness_measures)

        """

        for analysis in self.config["direct"]:
            logging.info(
                f"----------------------------- Started analyzing '{analysis['name']}'  -----------------------------"
            )
            starttime = time.time()

            if analysis["analysis"] == "direct":

                gdf = self.road_damage(
                    analysis
                )  # calls the coordinator for road damage calculation

            elif analysis["analysis"] == "effectiveness_measures":
                gdf = self.effectiveness_measures(analysis)

            else:
                gdf = []

            output_path = self.config["output"] / analysis["analysis"]
            if analysis["save_shp"]:
                shp_path = output_path / (analysis["name"].replace(" ", "_") + ".shp")
                save_gdf(gdf, shp_path)
            if analysis["save_csv"]:
                csv_path = output_path / (analysis["name"].replace(" ", "_") + ".csv")
                del gdf["geometry"]
                gdf.to_csv(csv_path, index=False)

            endtime = time.time()
            logging.info(
                f"----------------------------- Analysis '{analysis['name']}' finished. "
                f"Time: {str(round(endtime - starttime, 2))}s  -----------------------------"
            )

    def road_damage(self, analysis: dict) -> gpd.GeoDataFrame:
        """
        ### CONTROLER FOR CALCULATING THE ROAD DAMAGE

        Arguments:
            *analysis* (dict) : contains part of the settings from the analysis ini

        Returns:
            *result_gdf* (GeoDataFrame) : The original hazard dataframe with the result of the damage calculations added

        """
        # Open the network with hazard data
        # Dirty fix, Todo: figure out why this key does not exist under certaint conditions
        if (
            "base_network_hazard" not in self.graphs
        ):  # key is missing due to error in handler?
            self.graphs["base_network_hazard"] = None

        road_gdf = self.graphs["base_network_hazard"]
        if self.graphs["base_network_hazard"] is None:
            road_gdf = gpd.read_feather(self.config["files"]["base_network_hazard"])

        road_gdf.columns = rename_road_gdf_to_conventions(road_gdf.columns)

        # Find the hazard columns; these may be events or return periods
        val_cols = [
            col for col in road_gdf.columns if (col[0].isupper() and col[1] == "_")
        ]

        # Read the desired damage function
        damage_function = analysis["damage_curve"]

        # If you want to use manual damage functions, these need to be loaded first
        manual_damage_functions = None
        if analysis["damage_curve"] == "MAN":
            manual_damage_functions = ManualDamageFunctions()
            manual_damage_functions.find_damage_functions(
                folder=(self.config["input"] / "damage_functions")
            )
            manual_damage_functions.load_damage_functions()

        # Choose between event or return period based analysis
        if analysis["event_type"] == "event":

            event_gdf = DamageNetworkEvents(road_gdf, val_cols)
            event_gdf.main(
                damage_function=damage_function,
                manual_damage_functions=manual_damage_functions,
            )

            return event_gdf.gdf

        elif analysis["event_type"] == "return_period":
            return_period_gdf = DamageNetworkReturnPeriods(road_gdf, val_cols)
            return_period_gdf.main(
                damage_function=damage_function,
                manual_damage_functions=manual_damage_functions,
            )

            if "risk_calculation" in analysis:  # Check if risk_calculation is demanded
                if analysis["risk_calculation"] != "none":
                    return_period_gdf.control_risk_calculation(
                        mode=analysis["risk_calculation"]
                    )

            else:
                logging.info(
                    """No parameters for risk calculation are specified. 
                             Add key [risk_calculation] to analyses.ini."""
                )

            return return_period_gdf.gdf

        else:
            raise ValueError(
                """"The hazard calculation does not know 
            what to do if the analysis specifies {}""".format(
                    analysis["event_type"]
                )
            )

    def effectiveness_measures(self, analysis):
        """This function calculated the efficiency of measures. Input is a csv file with efficiency
        and a list of different aspects you want to check.
        """
        em = EffectivenessMeasures(self.config, analysis)
        effectiveness_dict = em.load_effectiveness_table(
            self.config["input"] / "direct"
        )

        if self.graphs["base_network_hazard"] is None:
            gdf_in = gpd.read_feather(self.config["files"]["base_network_hazard"])

        if analysis["create_table"] is True:
            df = em.create_feature_table(
                self.config["input"] / "direct" / analysis["file_name"]
            )
        else:
            df = em.load_table(
                self.config["input"] / "direct",
                analysis["file_name"].replace(".shp", ".csv"),
            )

        df = em.calculate_strategy_effectiveness(df, effectiveness_dict)
        df = em.knmi_correction(df)
        df_cba, costs_dict = em.cost_benefit_analysis(effectiveness_dict)
        df_cba.round(2).to_csv(
            self.config["output"] / analysis["analysis"] / "cost_benefit_analysis.csv",
            decimal=",",
            sep=";",
            index=False,
            float_format="%.2f",
        )
        df = em.calculate_cost_reduction(df, effectiveness_dict)
        df_costs = em.calculate_strategy_costs(df, costs_dict)
        df_costs = df_costs.astype(float).round(2)
        df_costs.to_csv(
            self.config["output"] / analysis["analysis"] / "output_analysis.csv",
            decimal=",",
            sep=";",
            index=False,
            float_format="%.2f",
        )
        gdf = gdf_in.merge(df, how="left", on="LinkNr")
        return gdf


def save_gdf(gdf, save_path):
    """Takes in a geodataframe object and outputs shapefiles at the paths indicated by edge_shp and node_shp

    Arguments:
        gdf [geodataframe]: geodataframe object to be converted
        edge_shp [str]: output path including extension for edges shapefile
        node_shp [str]: output path including extension for nodes shapefile
    Returns:
        None
    """
    # save to shapefile
    gdf.crs = "epsg:4326"  # TODO: decide if this should be variable with e.g. an output_crs configured

    for col in gdf.columns:
        if gdf[col].dtype == object and col != gdf.geometry.name:
            gdf[col] = gdf[col].astype(str)

    gdf.to_file(save_path, driver="ESRI Shapefile", encoding="utf-8")
    logging.info("Results saved to: {}".format(save_path))


# Todo: these should be moved
def test_construct_max_damage():
    max_damage = MaxDamageByRoadTypeByLane()
    path = Path(
        r"D:\Python\ra2ce\data\1010b_zuid_holland\input\damage_function\test\huizinga_max_damage.csv"
    )
    max_damage.from_csv(path, sep=";")
    return max_damage


def test_construct_damage_fraction():
    damage_fraction = DamageFractionUniform()
    path = Path(
        r"D:\Python\ra2ce\data\1010b_zuid_holland\input\damage_function\test\huizinga_damage_fraction_hazard_severity.csv"
    )
    damage_fraction.from_csv(path, sep=";")
    return damage_fraction


# max_damage = test_construct_max_damage()

# max_damage = test_construct_damage_fraction()


def rename_road_gdf_to_conventions(road_gdf_columns):
    """
    Rename the columns in the road_gdf to the conventions of the ra2ce documentation

    'eg' RP100_fr -> F_RP100_me
                   -> F_EV1_mi

    """
    cs = road_gdf_columns
    ### Handle return period columns
    new_cols = []
    for c in cs:
        if c.startswith("RP"):
            new_cols.append("F_" + c)
        else:
            new_cols.append(c)

    ### Todo add handling of events if this gives a problem
    return new_cols
