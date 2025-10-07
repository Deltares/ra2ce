import ast
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

            # Sort columns by name skipping any unnamed index columns that may have been added.
            _df = _df.reindex(
                sorted(_df.columns[~_df.columns.str.startswith("Unnamed")]), axis=1
            )

            # Sort values that contain lists (or list as string) to ensure consistent order.
            for _col in _df.select_dtypes(include=["object"]).columns:
                if (
                    _df[_col]
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

                    _df[_col] = _df[_col].apply(_sort_list)

            # Sort rows based on all columns to ensure consistent order.
            return _df.sort_values(by=_df.columns.to_list()).reset_index(drop=True)

        _df_ref = _get_normalized_content(self.reference_file)
        _df_res = _get_normalized_content(self.result_file)

        if len(_df_ref) != len(_df_res):
            raise AssertionError(
                f"CSV file {self.result_file.name} deviates in number of rows: {len(_df_ref)} != {len(_df_res)}"
            )

        _mismatches = ~((_df_ref == _df_res) | (_df_ref.isna() & _df_res.isna()))
        _first_mismatch_row = _mismatches.sum(axis=1).idxmax()
        if not _first_mismatch_row:
            return

        _mismatch_columns = _mismatches.columns[_mismatches.loc[_first_mismatch_row]]
        raise AssertionError(
            f"CSV file {self.result_file.name} deviates in content.\n"
            f"Reference:\n{_df_ref.loc[_first_mismatch_row]}\n"
            f"Result:\n{_df_res.loc[_first_mismatch_row]}\n"
            f"Mismatching columns: {_mismatch_columns}"
        )
