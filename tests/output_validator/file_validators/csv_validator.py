from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from tests.output_validator.file_validators.file_validator_protocol import (
    FileValidatorProtocol,
)
from tests.output_validator.file_validators.pandas_validator_base import (
    PandasValidatorBase,
)


@dataclass
class CsvValidator(FileValidatorProtocol, PandasValidatorBase):
    reference_file: Path
    result_file: Path

    def _read_file(self, file_path: Path) -> pd.DataFrame:
        _df = pd.read_csv(file_path)
        assert isinstance(_df, pd.DataFrame)
        return _df

    def __post_init__(self) -> None:

        _df_ref = self._get_normalized_content(self.reference_file)
        _df_res = self._get_normalized_content(self.result_file)

        if len(_df_ref) != len(_df_res):
            raise AssertionError(
                f"CSV file {self.result_file.name} deviates in number of rows: {len(_df_ref)} != {len(_df_res)}"
            )

        _mismatches = self._get_mismatches(_df_ref, _df_res)
        _first_mismatch_row = _mismatches.sum(axis=1).idxmax()
        if not _first_mismatch_row:
            return

        _mismatch_columns = _mismatches.columns[_mismatches.loc[_first_mismatch_row]]
        raise AssertionError(
            f"CSV file {self.result_file.name} deviates in content.\n"
            f"Reference:\n{_df_ref.loc[_first_mismatch_row]}\n"
            f"Result   :\n{_df_res.loc[_first_mismatch_row]}\n"
            f"Mismatching columns: {_mismatch_columns}"
        )
