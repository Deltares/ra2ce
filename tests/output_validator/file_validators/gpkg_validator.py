from pathlib import Path

import fiona
import geopandas as gpd

from .file_validator_protocol import FileValidatorProtocol


class GpkgValidator(FileValidatorProtocol):
    @staticmethod
    def validate(reference_file: Path, result_file: Path) -> None:
        _gdf_ref = gpd.read_file(reference_file)
        _gdf_res = gpd.read_file(result_file)

        if len(_gdf_ref) != len(_gdf_res):
            raise AssertionError(
                f"GPKG files {reference_file} and {result_file} differ in number of features (rows): {len(_gdf_ref)} != {len(_gdf_res)}"
            )

        _ref_schema = fiona.open(reference_file).schema
        _res_schema = fiona.open(result_file).schema
        if _ref_schema != _res_schema:
            raise AssertionError(
                f"GPKG files {reference_file} and {result_file} differ in schema (columns): {_ref_schema} != {_res_schema}"
            )

        _first_mismatch = (
            _gdf_ref.fillna("").ne(_gdf_res.fillna("")).sum(axis=1).idxmax()
        )
        if not _first_mismatch:
            return

        raise AssertionError(
            f"GPKG files {reference_file} and {result_file} differ at feature (row) {_first_mismatch}: {_gdf_res.loc[_first_mismatch].to_dict()}"
        )
