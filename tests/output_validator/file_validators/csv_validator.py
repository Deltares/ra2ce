from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from tests.output_validator.file_validators.file_validator_protocol import (
    FileValidatorProtocol,
)


@dataclass
class CsvValidator(FileValidatorProtocol):
    reference_file: Path
    result_file: Path

    def __post_init__(self) -> None:
        def _get_normalized_content(file_path: Path) -> pd.DataFrame:
            _df = pd.read_csv(file_path)
            # Sort columns skipping any unnamed index columns that may have been added.
            _df = _df.reindex(
                sorted(_df.columns[~_df.columns.str.startswith("Unnamed")]), axis=1
            )
            # Sort rows based on all columns to ensure consistent order.
            return _df.sort_values(by=_df.columns.to_list()).reset_index(drop=True)

        _df_ref = _get_normalized_content(self.reference_file)
        _df_res = _get_normalized_content(self.result_file)

        _first_mismatch = _df_ref.fillna("").ne(_df_res.fillna("")).sum(axis=1).idxmax()
        if not _first_mismatch:
            return

        raise AssertionError(
            f"CSV file {self.result_file.name} differs:\n"
            f"Reference: {_df_ref.loc[_first_mismatch].to_dict()}\n"
            f"Result: {_df_res.loc[_first_mismatch].to_dict()}"
        )
