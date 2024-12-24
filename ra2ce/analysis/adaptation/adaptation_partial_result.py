from __future__ import annotations

import logging
import math

from geopandas import GeoDataFrame, GeoSeries

from ra2ce.analysis.adaptation.adaptation_result_enum import AdaptationResultEnum
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)


class AdaptationPartialResult:
    """
    Class to represent the partial result of an adaptation analysis.
    """

    id_col: str
    data_frame: GeoDataFrame
    _key_col: str = "merge_key"

    def __init__(self, id_col: str | None, data_frame: GeoDataFrame | None) -> None:
        if id_col:
            self.id_col = id_col
        else:
            self.id_col = "link_id"

        if not isinstance(data_frame, GeoDataFrame) or data_frame.empty:
            self.data_frame = GeoDataFrame()
            return
        else:
            self.data_frame = data_frame

        # Add column to merge on, dropping the original column
        self.data_frame[self._key_col] = self.data_frame[self.id_col].apply(
            lambda x: str(x)
        )
        self.data_frame.drop(columns=[self.id_col], inplace=True)

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

    def get_option_column_name(
        self, option_id: str, col_type: AdaptationResultEnum | str
    ) -> str:
        if isinstance(col_type, AdaptationResultEnum):
            return f"{option_id}_{col_type.config_value}"
        return f"{option_id}_{col_type}"

    @classmethod
    def from_gdf_with_matched_col(
        cls,
        gdf_in: GeoDataFrame,
        id_col: str,
        regex: str,
        analysis_type: AnalysisDamagesEnum | AnalysisLossesEnum,
    ) -> AdaptationPartialResult:
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
        return cls(id_col, _gdf)

    def merge_partial_results(self, other: AdaptationPartialResult) -> None:
        if other.data_frame.empty:
            return

        if self.data_frame.empty:
            self.data_frame = other.data_frame
            return

        # Filter out duplicate columns
        for _col in self.standard_cols:
            if _col in other.data_frame.columns:
                other.data_frame.drop(columns=[_col], inplace=True)

        self.data_frame = self.data_frame.merge(
            other.data_frame, on=self._key_col, how="outer"
        ).fillna(math.nan)

    def set_option_id(self, option_id: str) -> None:
        for _col in self.result_cols:
            self.data_frame.rename(
                columns={_col: self.get_option_column_name(option_id, _col)},
                inplace=True,
            )

    def add_option_column(
        self, option_id: str, col_type: AdaptationResultEnum, column_data: GeoSeries
    ) -> None:
        self.data_frame[self.get_option_column_name(option_id, col_type)] = column_data

    def get_option_column(
        self, option_id: str, col_type: AdaptationResultEnum
    ) -> GeoSeries:
        return self.data_frame[self.get_option_column_name(option_id, col_type)]
