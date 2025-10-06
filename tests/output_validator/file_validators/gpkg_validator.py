import ast
from dataclasses import dataclass
from pathlib import Path

import fiona
import geopandas as gpd

from tests.output_validator.file_validators.file_validator_protocol import (
    FileValidatorProtocol,
)


@dataclass
class GpkgValidator(FileValidatorProtocol):
    reference_file: Path
    result_file: Path

    def __post_init__(self) -> None:
        def _get_sorted_content(file_path: Path) -> gpd.GeoDataFrame:
            _gdf = gpd.read_file(file_path)

            # Sort values that contain lists (or list as string) to ensure consistent order.
            for _col in _gdf.select_dtypes(include=["object"]).columns:
                if (
                    _gdf[_col]
                    .apply(lambda x: isinstance(x, (list, str)) and "[" in str(x))
                    .any()
                ):

                    def _sort_list(x):
                        if isinstance(x, list):
                            return sorted(x)
                        if isinstance(x, str) and x.startswith("[") and x.endswith("]"):
                            try:

                                _list_value = ast.literal_eval(x)
                                if isinstance(_list_value, list):
                                    return str(sorted(_list_value))
                            except (ValueError, SyntaxError):
                                pass
                        return x

                    _gdf[_col] = _gdf[_col].apply(_sort_list)

            # Sort rows based on all columns to ensure consistent order.
            return _gdf.sort_values(by=_gdf.columns.to_list()).reset_index(drop=True)

        _gdf_ref = _get_sorted_content(self.reference_file)
        _gdf_res = _get_sorted_content(self.result_file)

        if len(_gdf_ref) != len(_gdf_res):
            raise AssertionError(
                f"GPKG file {self.result_file.name} differs in number of rows: {len(_gdf_ref)} != {len(_gdf_res)}"
            )

        _ref_schema = fiona.open(self.reference_file).schema
        _res_schema = fiona.open(self.result_file).schema
        if _ref_schema != _res_schema:
            raise AssertionError(
                f"GPKG file {self.result_file.name} differs in columns.\n"
                f"Reference: {_ref_schema}\n"
                f"Result: {_res_schema}"
            )

        _mismatches = _gdf_ref.fillna("").ne(_gdf_res.fillna(""))
        _first_mismatch_row = _mismatches.sum(axis=1).idxmax()
        if not _first_mismatch_row:
            return

        _mismatch_columns = _mismatches.columns[_mismatches.loc[_first_mismatch_row]]
        raise AssertionError(
            f"GPKG file {self.result_file.name} differs in content on row {_first_mismatch_row}.\n"
            f"Reference: {_gdf_ref.loc[_first_mismatch_row][_mismatch_columns].to_dict()}\n"
            f"Result: {_gdf_res.loc[_first_mismatch_row][_mismatch_columns].to_dict()}"
        )
