import logging
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionDamages,
)
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.damages.analysis_damages_protocol import AnalysisDamagesProtocol
from ra2ce.network.graph_files.network_file import NetworkFile


class EffectivenessMeasures(AnalysisDamagesProtocol):
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
        self.result = None

        self.return_period = self.analysis.return_period  # years
        self.repair_costs = self.analysis.repair_costs  # euro
        self.evaluation_period = self.analysis.evaluation_period  # years
        self.interest_rate = self.analysis.interest_rate / 100  # interest rate
        self.btw = 1.21  # VAT multiplication factor to include taxes
        self._measures_csv = self.input_path.joinpath(
            "direct_damage", "effectiveness_measures.csv"
        )

        # perform checks on input while initializing class
        self._validate_input_params(self.input_path, self.analysis)

    def _validate_input_params(
        self, input_path: Path, analysis: AnalysisSectionDamages
    ) -> None:
        if analysis.file_name is None:
            _error = "Effectiveness of measures calculation: No input file configured. Please define an input file in the analysis.ini file."
            logging.error(_error)
            raise ValueError(_error)
        elif analysis.file_name.suffix != ".shp":
            _error = "Effectiveness of measures calculation: Wrong input file configured. Extension of input file is -{}-, needs to be -.shp- (shapefile)".format(
                analysis.file_name.suffix
            )
            logging.error(_error)
            raise ValueError(_error)
        elif not (input_path / "direct_damage" / analysis.file_name).exists():
            _error = "Effectiveness of measures calculation: Input file doesn't exist please place file in the following folder: {}".format(
                input_path / "direct_damage"
            )
            logging.error(_error)
            raise FileNotFoundError(input_path / "direct_damage" / analysis.file_name)
        elif not self._measures_csv.exists():
            _error = "Effectiveness of measures calculation: lookup table with effectiveness of measures doesnt exist. Please place the effectiveness_measures.csv file in the following folder: {}".format(
                input_path / "direct_damage"
            )
            logging.error(_error)
            raise FileNotFoundError(self._measures_csv)

    def _load_effectiveness_table(self) -> dict:
        """This function loads a CSV table containing effectiveness of the different aspects for a number of strategies"""
        df_lookup = pd.read_csv(self._measures_csv, index_col="strategies")
        return df_lookup.transpose().to_dict()

    def _create_feature_table(self, file_path: Path) -> pd.DataFrame:
        """This function loads a table of features from the input folder"""
        logging.info("Loading feature dataframe...")
        gdf = gpd.read_file(file_path, engine="pyogrio")
        logging.info("Dataframe loaded...")

        # cleaning up dataframe
        df = pd.DataFrame(gdf.drop(columns="geometry"))
        df = df[df["LinkNr"] != 0]
        df = df.sort_values(by=["LinkNr", "TARGET_FID"])
        df = df.rename(
            columns={
                "ver_hoog_m": "ver_hoger_m",
                "hwaafwho_m": "hwa_afw_ho_m",
                "slope_15_m": "slope_0015_m",
                "slope_1_m": "slope_001_m",
                "TARGET_FID": "target_fid",
                "Length": "length",
            }
        )
        df = df[
            [
                "LinkNr",
                "target_fid",
                "length",
                "dichtbij_m",
                "ver_hoger_m",
                "hwa_afw_ho_m",
                "gw_hwa_m",
                "slope_0015_m",
                "slope_001_m",
            ]
        ]

        # save as csv
        path, file = os.path.split(file_path)
        df.to_csv(os.path.join(path, file.replace(".gpkg", ".csv")), index=False)
        return df

    def _load_table(self, path: Path, file: str) -> pd.DataFrame:
        """This method reads the dataframe created from"""
        file_path = path / file
        df = pd.read_csv(file_path)
        return df

    def _knmi_correction(self, df: pd.DataFrame, duration: int = 60) -> pd.DataFrame:
        """This function corrects the length of each segment depending on a KNMI factor.
        This factor is calculated using an exponential relation and was calculated using an analysis on all line elements
        a relation is establisched for a 10 minute or 60 minute rainfall period
        With a boolean you can decide to export length or the coefficient itself
        max 0.26 en 0.17
        """
        if duration not in [10, 60]:
            _error_mssg = "Wrong duration configured, has to be 10 or 60"
            logging.error(_error_mssg)
            raise ValueError(_error_mssg)
        logging.info(
            "Applying knmi length correction with duration of rainfall of -{}- minutes".format(
                duration
            )
        )

        coefficients_lookup = {
            10: {"a": 1.004826523, "b": -0.000220199, "max": 0.17},
            60: {"a": 1.012786829, "b": -0.000169182, "max": 0.26},
        }

        coefficient = coefficients_lookup[duration]
        df["coefficient"] = coefficient["a"] * np.exp(coefficient["b"] * df["length"])
        df["coefficient"] = df["coefficient"].where(
            df["length"].astype(float) <= 8000, other=coefficient["max"]
        )
        return df

    def _calculate_effectiveness(
        self, df: pd.DataFrame, name: str = "standard"
    ) -> pd.DataFrame:
        """This function calculates effectiveness, based on a number of columns:
        'dichtbij_m', 'ver_hoger_m', 'hwa_afw_ho_m', 'gw_hwa_m', slope_0015_m' and 'slope_001_m'
        and contains the following steps:
        1. calculate the max of ver_hoger, hwa_afw_ho and gw_hwa columns --> verweg
        2. calculate maximum of slope0015 / 2 and slope 001 columns --> verkant
        3. calculate max of verweg, verkant and dichtbij
        4. calculate sum of verweg, verkant and dichtbij
        5. aggregate (sum) of values to LinkNr
        """
        _gevoelig_max_name = "{}_gevoelig_max".format(name)
        _gevoelig_sum_name = "{}_gevoelig_sum".format(name)

        # perform calculation of max length of ver weg elements and slope elements:
        df["slope_0015_m2"] = df["slope_0015_m"] / 2
        df["verweg_max"] = (
            df[["ver_hoger_m", "hwa_afw_ho_m", "gw_hwa_m"]].values.max(1).round(0)
        )
        df["verkant_max"] = df[["slope_0015_m2", "slope_001_m"]].values.max(1).round(0)

        # calculate gevoelig max and dum
        df[_gevoelig_max_name] = (
            df[["verweg_max", "verkant_max", "dichtbij_m"]].values.max(1).round(0)
        )
        df[_gevoelig_sum_name] = df["verweg_max"] + df["verkant_max"] + df["dichtbij_m"]

        # aggregate to link nr
        new_df = df[
            [
                "LinkNr",
                "length",
                "dichtbij_m",
                "ver_hoger_m",
                "hwa_afw_ho_m",
                "gw_hwa_m",
                "verweg_max",
                "verkant_max",
                _gevoelig_max_name,
                _gevoelig_sum_name,
            ]
        ]
        new_df = new_df.groupby(["LinkNr"]).sum()
        new_df["LinkNr"] = new_df.index
        new_df = new_df.reset_index(drop=True)

        return new_df[
            [
                "LinkNr",
                "length",
                "dichtbij_m",
                "ver_hoger_m",
                "hwa_afw_ho_m",
                "gw_hwa_m",
                "verweg_max",
                "verkant_max",
                _gevoelig_max_name,
                _gevoelig_sum_name,
            ]
        ]

    def _calculate_strategy_effectiveness(
        self, df: pd.DataFrame, effectiveness_dict: dict
    ) -> pd.DataFrame:
        """This function calculates the efficacy for each strategy"""

        columns = [
            "dichtbij",
            "ver_hoger",
            "hwa_afw_ho",
            "gw_hwa",
            "slope_0015",
            "slope_001",
        ]

        # calculate standard effectiveness without factors
        df_total = self._calculate_effectiveness(df, name="standard")

        df_blockage = pd.read_csv(
            self.input_path / "direct_damage" / "blockage_costs.csv"
        )
        df_total = df_total.merge(df_blockage, how="left", on="LinkNr")
        df_total["length"] = df_total[
            "afstand"
        ]  # TODO Remove this line as this is probably incorrect, just as a check

        # start iterating over different strategies in lookup dictionary
        for strategy in effectiveness_dict:
            logging.info("Calculating effectiveness of strategy: {}".format(strategy))
            lookup_dict = effectiveness_dict[strategy]
            df_temp = df.copy()

            # apply the effectiveness factor as read from the lookup table on each column:
            for col in columns:
                df_temp[col + "_m"] = df_temp[col + "_m"] * (1 - lookup_dict[col])

            # calculate the effectiveness and add as a new column to total dataframe
            df_new = self._calculate_effectiveness(df_temp, name=strategy)
            df_new = df_new.drop(
                columns={
                    "length",
                    "dichtbij_m",
                    "ver_hoger_m",
                    "hwa_afw_ho_m",
                    "gw_hwa_m",
                    "verweg_max",
                    "verkant_max",
                }
            )
            df_total = df_total.merge(df_new, how="left", on="LinkNr")

        return df_total

    def _calculate_cost_reduction(
        self, df: pd.DataFrame, effectiveness_dict: dict
    ) -> pd.DataFrame:
        """This function calculates the yearly costs and possible reduction"""

        strategies = [strategy for strategy in effectiveness_dict]
        strategies.insert(0, "standard")

        # calculate costs
        for strategy in strategies:
            if strategy != "standard":
                df["max_effectiveness_{}".format(strategy)] = 1 - (
                    df["{}_gevoelig_sum".format(strategy)] / df["standard_gevoelig_sum"]
                )
            df["return_period"] = self.return_period * df["coefficient"]
            df["repair_costs_{}".format(strategy)] = (
                df["{}_gevoelig_max".format(strategy)] * self.repair_costs
            )
            # Keys definition to avoid code duplication.
            _blockage_costs_strategy = "blockage_costs_{}".format(strategy)
            _yearly_blockage_costs_strategy = "yearly_blockage_costs_{}".format(
                strategy
            )
            _yearly_repair_costs_strategy = "yearly_repair_costs_{}".format(strategy)
            _total_costs_strategy = "total_costs_{}".format(strategy)

            df[_blockage_costs_strategy] = df["blockage_costs"]
            df[_yearly_repair_costs_strategy] = (
                df["repair_costs_{}".format(strategy)] / df["return_period"]
            )
            if strategy == "standard":
                df[_yearly_blockage_costs_strategy] = (
                    df[_blockage_costs_strategy] / df["return_period"]
                )
            else:
                df[_yearly_blockage_costs_strategy] = (
                    df[_blockage_costs_strategy]
                    / df["return_period"]
                    * (1 - df["max_effectiveness_{}".format(strategy)])
                )
            df[_total_costs_strategy] = (
                df[_yearly_repair_costs_strategy] + df[_yearly_blockage_costs_strategy]
            )
            if strategy != "standard":
                df["reduction_repair_costs_{}".format(strategy)] = (
                    df["yearly_repair_costs_standard"]
                    - df[_yearly_repair_costs_strategy]
                )
                df["reduction_blockage_costs_{}".format(strategy)] = (
                    df["yearly_blockage_costs_standard"]
                    - df[_yearly_blockage_costs_strategy]
                )
                df["reduction_costs_{}".format(strategy)] = (
                    df["total_costs_standard"] - df[_total_costs_strategy]
                )
                df["effectiveness_{}".format(strategy)] = 1 - (
                    df[_total_costs_strategy] / df["total_costs_standard"]
                )
        return df

    def _cost_benefit_analysis(self, effectiveness_dict) -> tuple[pd.DataFrame, dict]:
        """This method performs cost benefit analysis"""

        def _calc_npv(x: pd.DataFrame, cols: list[str]) -> float:
            pv = np.npv(self.interest_rate, [0] + list(x[cols]))
            return pv

        def _calc_npv_factor(factor: float) -> float:
            cols = np.linspace(
                1,
                1 + (factor * self.evaluation_period),
                self.evaluation_period,
                endpoint=False,
            )
            return np.npv(self.interest_rate, [0] + list(cols))

        def _calc_cash_flow(x, cols):
            cash_flow = x[cols].sum() + x["investment"]
            return cash_flow

        df_cba = pd.DataFrame.from_dict(effectiveness_dict).transpose()
        df_cba["strategy"] = df_cba.index
        df_cba = df_cba.drop(
            columns=[
                "dichtbij",
                "ver_hoger",
                "hwa_afw_ho",
                "gw_hwa",
                "slope_0015",
                "slope_001",
            ]
        )
        df_cba["investment"] = df_cba["investment"] * -1

        df_cba["lifespan"] = df_cba["lifespan"].astype(int)
        for col in ["om_pv", "pv", "cash_flow"]:
            df_cba.insert(0, col, 0)

        # add years
        for year in range(1, self.evaluation_period + 1):
            df_cba[str(year)] = df_cba["investment"].where(
                np.mod(year, df_cba["lifespan"]) == 0, other=0
            )
        year_cols = [str(year) for year in range(1, self.evaluation_period + 1)]

        df_cba["om_pv"] = df_cba.apply(lambda x: _calc_npv(x, year_cols), axis=1)
        df_cba["pv"] = df_cba["om_pv"] + df_cba["investment"]
        df_cba["cash_flow"] = df_cba.apply(
            lambda x: _calc_cash_flow(x, year_cols), axis=1
        )
        df_cba["costs"] = df_cba["pv"] * self.btw
        df_cba["costs_pmt"] = (
            np.pmt(
                self.interest_rate, df_cba["lifespan"], df_cba["investment"], when="end"
            )
            * self.btw
        )
        df_cba = df_cba.round(2)

        costs_dict = df_cba[["costs", "on_column"]].to_dict()
        costs_dict["npv_factor"] = _calc_npv_factor(self.climate_factor)

        return df_cba, costs_dict

    def _calculate_strategy_costs(
        self, df: pd.DataFrame, costs_dict: dict
    ) -> pd.DataFrame:
        """Method to calculate costs, benefits with net present value"""

        costs = costs_dict["costs"]
        columns = costs_dict["on_column"]

        def _columns_check(df: pd.DataFrame, columns: list[str]) -> bool:
            cols_check = []
            for col in columns:
                cols_check.extend(columns[col].split(";"))
            df_cols = list(df.columns)

            if any([True for col in cols_check if col not in df_cols]):
                cols = [col for col in cols_check if col not in df_cols]
                _error_mssg = "Wrong column configured in effectiveness_measures csv file. column {} is not available in imported sheet.".format(
                    cols
                )
                logging.error(_error_mssg)
                raise ValueError(_error_mssg)
            return True

        _columns_check(df, columns)
        strategies = {col: columns[col].split(";") for col in columns}

        for strategy in strategies:
            df["{}_benefits".format(strategy)] = (
                df["reduction_costs_{}".format(strategy)] * costs_dict["npv_factor"]
            )
            select_col = strategies[strategy]
            # Definition of key strings to avoid code duplication
            _strategy_costs = "{}_costs".format(strategy)

            if len(select_col) == 1:
                df[_strategy_costs] = df[select_col[0]] * costs[strategy] * -1 / 1000
            if len(select_col) > 1:
                df[_strategy_costs] = (
                    (df[select_col[0]] - df[select_col[1]])
                    * costs[strategy]
                    * -1
                    / 1000
                )
                df[_strategy_costs] = df[_strategy_costs].where(
                    df[_strategy_costs] > 1, other=np.nan
                )
            df["{}_bc_ratio".format(strategy)] = (
                df["{}_benefits".format(strategy)] / df[_strategy_costs]
            )

        return df

    def execute(self) -> None:
        """This function calculated the efficiency of measures. Input is a csv file with efficiency
        and a list of different aspects you want to check.
        """
        effectiveness_dict = self._load_effectiveness_table()

        gdf_in = self.graph_file_hazard.get_graph()

        if self.analysis.create_table:
            df = self._create_feature_table(
                self.input_path.joinpath("direct_damage", self.analysis.file_name)
            )
        else:
            df = self._load_table(
                self.input_path.joinpath("direct_damage"),
                self.analysis.file_name.replace(".gpkg", ".csv"),
            )

        df = self._calculate_strategy_effectiveness(df, effectiveness_dict)
        df = self._knmi_correction(df)
        df_cba, costs_dict = em.cost_benefit_analysis(effectiveness_dict)
        df_cba.round(2).to_csv(
            self.output_path.joinpath(
                self.analysis.analysis.config_value,
                "cost_benefit_analysis.csv",
            ),
            decimal=",",
            sep=";",
            index=False,
            float_format="%.2f",
        )
        df = self._calculate_cost_reduction(df, effectiveness_dict)
        df_costs = self._calculate_strategy_costs(df, costs_dict)
        df_costs = df_costs.astype(float).round(2)
        df_costs.to_csv(
            self.output_path.joinpath(
                self.analysis.analysis.config_value, "output_analysis.csv"
            ),
            decimal=",",
            sep=";",
            index=False,
            float_format="%.2f",
        )

        return gdf_in.merge(df, how="left", on="LinkNr")
