from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd

from tests.output_validator.file_validators.file_validator_protocol import (
    FileValidatorProtocol,
)


@dataclass
class FeatherValidator(FileValidatorProtocol):
    reference_file: Path
    result_file: Path

    def __post_init__(self) -> None:
        def _get_normalized_content(file_path: Path) -> gpd.GeoDataFrame:
            _gdf = gpd.read_feather(file_path)
            assert isinstance(_gdf, gpd.GeoDataFrame)
            return _gdf

        _gdf_ref = _get_normalized_content(self.reference_file)
        _gdf_res = _get_normalized_content(self.result_file)

        if len(_gdf_ref) != len(_gdf_res):
            raise AssertionError(
                f"GPKG file {self.result_file.name} deviates in number of rows: {len(_gdf_ref)} != {len(_gdf_res)}"
            )

        _mismatches = ~((_gdf_ref == _gdf_res) | (_gdf_ref.isna() & _gdf_res.isna()))
        _first_mismatch_row = _mismatches.sum(axis=1).idxmax()
        if not _first_mismatch_row:
            return

        _mismatch_columns = _mismatches.columns[_mismatches.loc[_first_mismatch_row]]
        raise AssertionError(
            f"Feather file {self.result_file.name} deviates in content.\n"
            f"Reference: {_gdf_ref.loc[_first_mismatch_row][_mismatch_columns].to_dict()}\n"
            f"Result: {_gdf_res.loc[_first_mismatch_row][_mismatch_columns].to_dict()}"
        )
