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
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

from geopandas import GeoDataFrame
from pandas import Series

from ra2ce.analysis.adaptation.adaptation_result_enum import AdaptationResultEnum
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)


@dataclass
class AdaptationPartialResult:
    """
    Class to represent the partial result of an adaptation analysis.
    """

    option_id: str = ""
    id_col: str = "link_id"
    data_frame: GeoDataFrame = field(default_factory=GeoDataFrame)
    _key_col: str = "merge_key"

    def __post_init__(self) -> None:
        if self.data_frame.empty:
            return

        # Add column to merge on
        self.data_frame[self._key_col] = self.data_frame[self.id_col].apply(
            lambda x: str(x)
        )

        # Set geometry column
        if "geometry" not in self.data_frame.columns:
            logging.warning("No geometry column found in dataframe.")
            return
        self.data_frame.set_geometry("geometry")

    @property
    def standard_cols(self) -> list[str]:
        return [self.id_col, "geometry"]

    @property
    def result_cols(self) -> list[str]:
        return [
            _col
            for _col in self.data_frame.columns
            if _col not in self.standard_cols + [self._key_col]
        ]

    @classmethod
    def from_input_gdf(cls, gdf_in: GeoDataFrame) -> AdaptationPartialResult:
        """
        Create a new object from a GeoDataFrame.

        Args:
            gdf_in (GeoDataFrame): The input GeoDataFrame.

        Returns:
            AdaptationPartialResult: The object with the input data.
        """
        return cls(
            id_col=cls.id_col,
            data_frame=GeoDataFrame(gdf_in.filter(items=[cls.id_col, "geometry"])),
        )

    @classmethod
    def from_gdf_with_matched_col(
        cls,
        gdf_in: GeoDataFrame,
        id_col: str,
        regex: str,
        analysis_type: AnalysisDamagesEnum | AnalysisLossesEnum,
    ) -> AdaptationPartialResult:
        """
        Create a new object from a GeoDataFrame with a column matching a regex.

        Args:
            gdf_in (GeoDataFrame): The input GeoDataFrame.
            id_col (str): The ID column.
            regex (str): The pattern to match.
            analysis_type (AnalysisDamagesEnum | AnalysisLossesEnum): The type of the input analysis.

        Returns:
            AdaptationPartialResult: The object with the matched column.
        """
        _result_cols = gdf_in.filter(regex=regex).columns
        _gdf = gdf_in[[id_col, "geometry"]].copy()
        if _result_cols.empty:
            logging.warning(
                "No column found in dataframe matching the regex %s for analaysis %s. Returning NaN.",
                regex,
                analysis_type.config_value,
            )
            _gdf[analysis_type.config_value] = math.nan
        else:
            _gdf[analysis_type.config_value] = gdf_in[_result_cols[0]]
        return cls(id_col=id_col, data_frame=_gdf)

    def merge_partial_results(self, other: AdaptationPartialResult) -> None:
        """
        Merge the partial results of another analysis into this one.

        Args:
            other (AdaptationPartialResult): The other partial analysis results to merge.
        """
        if other.data_frame.empty:
            return

        if self.data_frame.empty:
            self.data_frame = other.data_frame
            return

        # If results from 2 different options are merged, reset the option ID
        if self.option_id and self.option_id != other.option_id:
            self.option_id = ""

        # Filter out duplicate columns
        for _col in self.standard_cols:
            if _col in other.data_frame.columns:
                other.data_frame.drop(columns=[_col], inplace=True)

        self.data_frame = self.data_frame.merge(
            other.data_frame, on=self._key_col, how="outer"
        ).fillna(math.nan)

    def _get_option_column_name(
        self, option_id: str, col_type: AdaptationResultEnum | str
    ) -> str:
        if isinstance(col_type, AdaptationResultEnum):
            return f"{option_id}_{col_type.config_value}"
        return f"{option_id}_{col_type}"

    def add_option_id(self, option_id: str) -> None:
        """
        Add the option ID to the result column names.

        Args:
            option_id (str): The option ID.
        """
        self.option_id = option_id
        for _col in self.result_cols:
            self.data_frame.rename(
                columns={_col: self._get_option_column_name(option_id, _col)},
                inplace=True,
            )

    def put_option_column(
        self, option_id: str, col_type: AdaptationResultEnum, column_data: Series
    ) -> None:
        """
        Add a data column to the result for a specific adaptation option.

        Args:
            option_id (str): The ID of the adaptation option.
            col_type (AdaptationResultEnum): The type of the column.
            column_data (Series): The data to add.
        """
        self.data_frame[self._get_option_column_name(option_id, col_type)] = column_data

    def get_option_column(
        self, option_id: str, col_type: AdaptationResultEnum
    ) -> Series:
        """
        Get a data column from the result for a specific adaptation option.

        Args:
            option_id (str): The ID of the adaptation option.
            col_type (AdaptationResultEnum):

        Returns:
            Series: The data column.
        """
        return self.data_frame[self._get_option_column_name(option_id, col_type)]
