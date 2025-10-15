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
    It wraps a GeoDataFrame with the results of the analysis and intermediate calculations.
    """

    option_id: str
    data_frame: GeoDataFrame = field(default_factory=GeoDataFrame)
    _id_col: str = "rfid"
    _key_col: str = "merge_key"

    def __post_init__(self) -> None:
        if self.data_frame.empty:
            return

        # Add column as string representation of _id_col to merge on (needed because "rfid" can contain objects)
        self.data_frame[self._key_col] = self.data_frame[self._id_col].apply(
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
        return self.__class__(
            option_id=self.option_id, data_frame=self.data_frame.copy()
        ).__iadd__(other)

    def __iadd__(
        self, other: AdaptationOptionPartialResult
    ) -> AdaptationOptionPartialResult:
        if other.data_frame.empty:
            # Nothing to add
            return self

        if self.data_frame.empty:
            # Take data from the other object
            self.option_id = other.option_id
            self.data_frame = other.data_frame
            return self

        if self.option_id != other.option_id:
            raise ValueError(
                "Cannot merge partial results from different adaptation options."
            )

        # Filter out duplicate columns (drop from the one with the least rows)
        for _col in self.standard_cols:
            if _col in other.data_frame.columns:
                if self.data_frame.shape[0] >= other.data_frame.shape[0]:
                    other.data_frame.drop(columns=[_col], inplace=True)
                else:
                    self.data_frame.drop(columns=[_col], inplace=True)

        # Merge the dataframes on the key column
        _merged = self.data_frame.merge(
            other.data_frame, on=self._key_col, how="outer"
        ).fillna(math.nan)

        # Restore the original order based on the dataframe with the most rows
        if self.data_frame.shape[1] >= other.data_frame.shape[1]:
            self.data_frame = (
                _merged.set_index(self._key_col)
                .reindex(self.data_frame[self._key_col])
                .reset_index()
            )
        else:
            self.data_frame = (
                _merged.set_index(self._key_col)
                .reindex(other.data_frame[self._key_col])
                .reset_index()
            )

        return self

    def __eq__(self, other: AdaptationOptionPartialResult) -> bool:
        """
        Check if both object's dataframes have the same key column.

        Args:
            other (AdaptationOptionPartialResult): The object to compare with.

        Returns:
            bool: True if the key columns are equal.
        """
        return self.data_frame[self._key_col].equals(other.data_frame[self._key_col])

    @property
    def standard_cols(self) -> list[str]:
        return [self._id_col, "geometry"]

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
        Create a new object from an input GeoDataFrame.

        Args:
            gdf_in (GeoDataFrame): The input GeoDataFrame.

        Returns:
            AdaptationOptionPartialResult: The object with the input data.
        """
        return cls(
            option_id=option_id,
            data_frame=GeoDataFrame(gdf_in.filter(items=[cls._id_col, "geometry"])),
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
            _result.add_column(analysis_type, math.nan)
        else:
            _result.add_column(analysis_type, gdf_in[_result_cols[0]])

        return _result

    def _get_column_name(
        self, col_type: AdaptationResultEnum | AnalysisDamagesEnum | AnalysisLossesEnum
    ) -> str:
        return f"{self.option_id}_{col_type.config_value}"

    def add_column(
        self,
        col_type: AdaptationResultEnum | AnalysisDamagesEnum | AnalysisLossesEnum,
        column_data: Series,
    ) -> None:
        """
        Add a data column to the result.

        Args:
            col_type (AdaptationResultEnum | AnalysisDamagesEnum | AnalysisLossesEnum): The type of the column.
            column_data (Series): The data to add.
        """
        self.data_frame[self._get_column_name(col_type)] = column_data

    def get_column(self, col_type: AdaptationResultEnum) -> Series:
        """
        Get a data column from the result.

        Args:
            col_type (AdaptationResultEnum): The type of the column.

        Returns:
            Series: The data column.
        """
        return self.data_frame[self._get_column_name(col_type)]
