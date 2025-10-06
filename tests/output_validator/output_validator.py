from pathlib import Path
from typing import Iterator, Optional

from tests.output_validator.file_validators.csv_validator import CsvValidator
from tests.output_validator.file_validators.feather_validator import FeatherValidator
from tests.output_validator.file_validators.file_validator_protocol import (
    FileValidatorProtocol,
)
from tests.output_validator.file_validators.gpkg_validator import GpkgValidator
from tests.output_validator.file_validators.json_validator import JsonValidator
from tests.output_validator.file_validators.pfile_validator import PfileValidator
from tests.output_validator.file_validators.xlsx_validator import XlsxValidator


class OutputValidator:
    reference_path: Path
    result_path: Path

    def __init__(
        self, result_path: Path, reference_path: Optional[Path] = None
    ) -> None:
        self.result_path = result_path
        self.reference_path = reference_path or result_path.joinpath("reference")

    def _get_file_validator(self, file: Path) -> type[FileValidatorProtocol]:
        if file.suffix == ".csv":
            return CsvValidator
        if file.suffix == ".gpkg":
            return GpkgValidator
        if file.suffix == ".json":
            return JsonValidator
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

        _validator = self._get_file_validator(file)
        _validator(_reference_file, _result_file).validate()

    def _get_relative_paths(
        self, base: Path, folder: Optional[Path] = None
    ) -> Iterator[Path]:
        # Get relative paths of all files in the folder (recursively).
        if not folder:
            folder = base

        # If `static` folder is present, handle this one first to detect network problems first.
        _static_folder = "static"
        if folder.joinpath(_static_folder).is_dir():
            yield from self._get_relative_paths(base, folder.joinpath(_static_folder))

        for _item in folder.iterdir():
            if _item.name == _static_folder:
                continue
            if _item.is_file():
                yield _item.relative_to(base)
            else:
                yield from self._get_relative_paths(base, _item)

    def validate_results(self) -> None:
        if not self.reference_path or not self.reference_path.is_dir():
            raise FileNotFoundError(f"Reference path {self.reference_path} not found.")
        for _ref_file in self._get_relative_paths(self.reference_path):
            self._check_result_file(_ref_file)
