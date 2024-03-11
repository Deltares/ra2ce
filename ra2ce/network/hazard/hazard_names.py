from pathlib import Path

import pandas as pd

FILE_NAME_KEY = "File name"
RA2CE_NAME_KEY = "RA2CE name"


class HazardNames:
    names_df: pd.DataFrame
    names: list[str]

    def __init__(self, hazard_names_df: pd.DataFrame, hazard_names: list[str]) -> None:
        self.names_df = hazard_names_df
        self.names = hazard_names

    @classmethod
    def from_file(cls, hazard_names_file: Path):
        if hazard_names_file.is_file():
            _names_df = pd.read_excel(hazard_names_file)
            _names = _names_df[FILE_NAME_KEY].tolist()
        else:
            _names_df = pd.DataFrame(data=None)
            _names = []
        return cls(_names_df, _names)

    def get_name(self, hazard: str) -> str:
        return self.names_df.loc[
            self.names_df[FILE_NAME_KEY] == hazard,
            RA2CE_NAME_KEY,
        ].values[0]
