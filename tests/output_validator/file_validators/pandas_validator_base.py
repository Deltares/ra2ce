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
        return ~(
            (df1 == df2)
            | (df1.isna() & df2.isna())
            | np.isclose(df1, df2, rtol=1e-6, equal_nan=True)
        )
