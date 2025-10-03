from pathlib import Path
from typing import Iterator, Optional

from tests.output_validator.csv_validator import CsvValidator
from tests.output_validator.feather_validator import FeatherValidator
from tests.output_validator.file_validator_protocol import FileValidatorProtocol
from tests.output_validator.gpkg_validator import GpkgValidator
from tests.output_validator.pfile_validator import PfileValidator
from tests.output_validator.xlsx_validator import XlsxValidator


class OutputValidator:
    reference_path: Path
    result_path: Path

    def __init__(
        self, result_path: Path, reference_path: Optional[Path] = None
    ) -> None:
        self.result_path = result_path
        self.reference_path = reference_path or result_path.joinpath("reference")

    def _get_file_validator(self, file: Path) -> FileValidatorProtocol:
        if file.suffix == ".csv":
            return CsvValidator
        if file.suffix == ".gpkg":
            return GpkgValidator
        if file.suffix == ".p":
            return PfileValidator
        if file.suffix == ".feather":
            return FeatherValidator
        if file.suffix == ".xlsx":
            return XlsxValidator
        raise NotImplementedError(
            f"No validator implemented for file type {file.suffix}"
        )

    def _check_result_file(self, file: Path) -> None:
        _reference_file = self.reference_path.joinpath(file)
        _result_file = self.result_path.joinpath(file)
        assert _result_file.is_file(), f"Path does not exist: {file}"

        self._get_file_validator(file).validate(_reference_file, _result_file)

    def _get_relative_paths(
        self, base: Path, folder: Optional[Path] = None
    ) -> Iterator[Path]:
        if not folder:
            folder = base
        for _item in folder.iterdir():
            if _item.is_file():
                yield _item.relative_to(base)
            else:
                yield from self._get_relative_paths(base, _item)

    def validate_results(self) -> None:
        if not self.reference_path or not self.reference_path.is_dir():
            raise FileNotFoundError(f"Reference path {self.reference_path} not found.")
        for _ref_file in self._get_relative_paths(self.reference_path):
            self._check_result_file(_ref_file)
