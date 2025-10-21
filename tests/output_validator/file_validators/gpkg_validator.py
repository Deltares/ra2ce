from dataclasses import dataclass
from pathlib import Path

import fiona
import geopandas as gpd

from tests.output_validator.file_validators.file_validator_protocol import (
    FileValidatorProtocol,
)
from tests.output_validator.file_validators.pandas_validator_base import (
    PandasValidatorBase,
)


@dataclass
class GpkgValidator(FileValidatorProtocol, PandasValidatorBase):
    reference_file: Path
    result_file: Path

    def _read_file(self, file_path: Path) -> gpd.GeoDataFrame:
        _gdf = gpd.read_file(file_path)
        assert isinstance(_gdf, gpd.GeoDataFrame)
        return _gdf

    def __post_init__(self) -> None:
        _gdf_ref = self._get_normalized_content(self.reference_file)
        _gdf_res = self._get_normalized_content(self.result_file)

        if len(_gdf_ref) != len(_gdf_res):
            raise AssertionError(
                f"GPKG file {self.result_file.name} deviates in number of rows: {len(_gdf_ref)} != {len(_gdf_res)}"
            )

        _ref_schema = fiona.open(self.reference_file).schema
        _res_schema = fiona.open(self.result_file).schema
        if sorted(_ref_schema) != sorted(_res_schema):
            raise AssertionError(
                f"GPKG file {self.result_file.name} deviates in columns.\n"
                f"Reference: {_ref_schema}\n"
                f"Result   : {_res_schema}"
            )

        _mismatches = self._get_mismatches(_gdf_ref, _gdf_res)
        _first_mismatch_row = _mismatches.sum(axis=1).idxmax()
        if not _first_mismatch_row:
            return

        _mismatch_columns = _mismatches.columns[_mismatches.loc[_first_mismatch_row]]
        raise AssertionError(
            f"GPKG file {self.result_file.name} deviates in content.\n"
            f"Reference row:\n{_gdf_ref.loc[_first_mismatch_row]}\n"
            f"Result row   :\n{_gdf_res.loc[_first_mismatch_row]}\n"
            f"Mismatching columns: {_mismatch_columns}\n"
            f"Total mismatches: {_mismatches.sum().sum()} of {_gdf_ref.shape[0] * _gdf_ref.shape[1]} values"
        )
