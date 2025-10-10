import ast
from abc import ABC
from pathlib import Path

import numpy as np
import pandas as pd


class PandasValidatorBase(ABC):
    def _read_file(self, file_path: Path):
        raise NotImplementedError

    def _get_normalized_content(self, file_path: Path) -> pd.DataFrame:
        _df = self._read_file(file_path)

        # Sort columns by name skipping any unnamed index columns that may have been added.
        _df = _df.reindex(
            sorted(_df.columns[~_df.columns.str.startswith("Unnamed")]), axis=1
        )

        # Convert None to np.nan for consistent comparison.
        _df = _df.applymap(lambda x: np.nan if x is None else x)

        # Sort values that contain lists (or list as string) to ensure consistent order.
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

        for _col in _df.select_dtypes(include=["object"]).columns:
            if (
                _df[_col]
                .apply(lambda x: isinstance(x, (list, str)) and "[" in str(x))
                .any()
            ):
                _df[_col] = _df[_col].apply(_sort_list)

        # Sort rows based on all columns to ensure consistent order.
        return _df.sort_values(by=_df.columns.to_list()).reset_index(drop=True)

    def _get_mismatches(self, df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        _mismatches = pd.DataFrame(False, index=df1.index, columns=df1.columns)
        for col in df1.columns:
            if pd.api.types.is_numeric_dtype(df1[col]):
                # Compare numeric columns with tolerance
                _mismatches[col] = ~(
                    (df1[col].isna() & df2[col].isna())
                    | np.isclose(df1[col], df2[col], rtol=1e-5, equal_nan=True)
                )
            else:
                # Compare non-numeric columns by exact equality or both NaN
                _mismatches[col] = ~(
                    (df1[col] == df2[col]) | (df1[col].isna() & df2[col].isna())
                )
        return _mismatches
