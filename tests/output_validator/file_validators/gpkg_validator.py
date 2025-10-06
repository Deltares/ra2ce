from pathlib import Path

import fiona
import geopandas as gpd

from tests.output_validator.file_validators.file_validator_protocol import (
    FileValidatorProtocol,
)


class GpkgValidator(FileValidatorProtocol):
    reference_file: Path
    result_file: Path

    def __init__(self, reference_file: Path, result_file: Path):
        self.reference_file = reference_file
        self.result_file = result_file

    def validate(self) -> None:
        _gdf_ref = gpd.read_file(self.reference_file)
        _gdf_res = gpd.read_file(self.result_file)

        if len(_gdf_ref) != len(_gdf_res):
            raise AssertionError(
                f"GPKG file {self.result_file.name} differs in number of rows: {len(_gdf_ref)} != {len(_gdf_res)}"
            )

        _ref_schema = fiona.open(self.reference_file).schema
        _res_schema = fiona.open(self.result_file).schema
        if _ref_schema != _res_schema:
            raise AssertionError(
                f"GPKG file {self.result_file.name} differs in columns: {_ref_schema} != {_res_schema}"
            )

        _first_mismatch = (
            _gdf_ref.fillna("").ne(_gdf_res.fillna("")).sum(axis=1).idxmax()
        )
        if not _first_mismatch:
            return

        raise AssertionError(
            f"GPKG file {self.result_file.name} differs in ccontent:\n"
            f"Reference: {_gdf_ref.loc[_first_mismatch].to_dict()}\n"
            f"Result: {_gdf_res.loc[_first_mismatch].to_dict()}"
        )
