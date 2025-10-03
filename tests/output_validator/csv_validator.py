from pathlib import Path

import pandas as pd

from tests.output_validator.file_validator_protocol import FileValidatorProtocol


class CsvValidator(FileValidatorProtocol):
    @staticmethod
    def validate(reference_file: Path, result_file: Path) -> None:
        _pd_ref = pd.read_csv(reference_file)
        _pd_res = pd.read_csv(result_file)

        _first_mismatch = _pd_ref.ne(_pd_res).first_valid_index()
        if not _first_mismatch:
            return

        raise AssertionError(
            f"CSV files {reference_file} and {result_file} differ at row {_first_mismatch}."
        )
