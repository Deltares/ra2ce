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
class AdaptationOptionPartialResult:
    """
    Class to represent the partial result of an adaptation analysis.
    """

    option_id: str
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

    def __add__(
        self, other: AdaptationOptionPartialResult
    ) -> AdaptationOptionPartialResult:
        _result = self.__class__(
            option_id=self.option_id,
            id_col=self.id_col,
            data_frame=self.data_frame.copy(),
        )
        _result._merge_partial_results(other)
        return _result

    def __iadd__(
        self, other: AdaptationOptionPartialResult
    ) -> AdaptationOptionPartialResult:
        self._merge_partial_results(other)
        return self

    def _merge_partial_results(self, other: AdaptationOptionPartialResult) -> None:
        """
        Merge the partial results of another analysis into this one.

        Args:
            other (AdaptationOptionPartialResult): The other partial analysis results to merge.
        """
        if other.data_frame.empty:
            return

        if self.data_frame.empty:
            self.option_id = other.option_id
            self.data_frame = other.data_frame
            return

        if self.option_id != other.option_id:
            raise ValueError(
                "Cannot merge partial results from different adaptation options."
            )

        # Filter out duplicate columns
        for _col in self.standard_cols:
            if _col in other.data_frame.columns:
                other.data_frame.drop(columns=[_col], inplace=True)

        self.data_frame = self.data_frame.merge(
            other.data_frame, on=self._key_col, how="outer"
        ).fillna(math.nan)

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
    def from_input_gdf(
        cls, option_id: str, gdf_in: GeoDataFrame
    ) -> AdaptationOptionPartialResult:
        """
        Create a new object from a GeoDataFrame.

        Args:
            gdf_in (GeoDataFrame): The input GeoDataFrame.

        Returns:
            AdaptationOptionPartialResult: The object with the input data.
        """
        return cls(
            option_id=option_id,
            id_col=cls.id_col,
            data_frame=GeoDataFrame(gdf_in.filter(items=[cls.id_col, "geometry"])),
        )

    @classmethod
    def from_gdf_with_matched_col(
        cls,
        option_id: str,
        gdf_in: GeoDataFrame,
        regex: str,
        analysis_type: AnalysisDamagesEnum | AnalysisLossesEnum,
    ) -> AdaptationOptionPartialResult:
        """
        Create a new object from a GeoDataFrame with a column matching a regex.

        Args:
            option_id (str): The ID of the adaptation option.
            gdf_in (GeoDataFrame): The input GeoDataFrame.
            regex (str): The pattern to match.
            analysis_type (AnalysisDamagesEnum | AnalysisLossesEnum): The type of the input analysis.

        Returns:
            AdaptationOptionPartialResult: The object with the matched column.
        """
        _result = cls.from_input_gdf(option_id, gdf_in)
        _result_cols = gdf_in.filter(regex=regex).columns
        if _result_cols.empty:
            logging.warning(
                "No column found in dataframe matching the regex %s for analaysis %s. Returning NaN.",
                regex,
                analysis_type.config_value,
            )
            _result.add_column(analysis_type.config_value, math.nan)
        else:
            _result.add_column(analysis_type.config_value, gdf_in[_result_cols[0]])

        return _result

    def _get_column_name(self, col_type: AdaptationResultEnum | str) -> str:
        if isinstance(col_type, AdaptationResultEnum):
            return f"{self.option_id}_{col_type.config_value}"
        return f"{self.option_id}_{col_type}"

    def add_column(
        self, col_type: AdaptationResultEnum | str, column_data: Series
    ) -> None:
        """
        Add a data column to the result.

        Args:
            col_type (AdaptationResultEnum): The type of the column.
            column_data (Series): The data to add.
        """
        self.data_frame[self._get_column_name(col_type)] = column_data

    def get_column(self, col_type: AdaptationResultEnum | str) -> Series:
        """
        Get a data column from the result.

        Args:
            col_type (AdaptationResultEnum):

        Returns:
            Series: The data column.
        """
        return self.data_frame[self._get_column_name(col_type)]
