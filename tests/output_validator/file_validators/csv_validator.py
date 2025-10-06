from pathlib import Path

import pandas as pd

from .file_validator_protocol import FileValidatorProtocol


class CsvValidator(FileValidatorProtocol):
    @staticmethod
    def validate(reference_file: Path, result_file: Path) -> pd.DataFrame:
        def _get_sorted_content(file_path: Path) -> pd.DataFrame:
            _df = pd.read_csv(file_path)
            # Sort columns skipping any unnamed index columns that may have been added.
            _df = _df.reindex(
                sorted(_df.columns[~_df.columns.str.startswith("Unnamed")]), axis=1
            )
            # Sort rows based on all columns to ensure consistent order.
            return _df.sort_values(by=_df.columns.to_list()).reset_index(drop=True)

        _df_ref = _get_sorted_content(reference_file)
        _df_res = _get_sorted_content(result_file)

        _first_mismatch = _df_ref.fillna("").ne(_df_res.fillna("")).sum(axis=1).idxmax()
        if not _first_mismatch:
            return

        raise AssertionError(
            f"CSV files {reference_file} and {result_file} differ at row {_first_mismatch}: {_df_res.loc[_first_mismatch].to_dict()}"
        )
