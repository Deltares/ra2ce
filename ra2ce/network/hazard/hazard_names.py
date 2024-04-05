"""
                    GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

    Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023 Stichting Deltares

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper

FILE_NAME_KEY = "File name"
RA2CE_NAME_KEY = "RA2CE name"


@dataclass
class HazardNames:
    names_df: pd.DataFrame

    @classmethod
    def from_file(cls, hazard_names_file: Path) -> HazardNames:
        """
        Create a HazardNames object from a file.

        Args:
            hazard_names_file (Path): Path to the files with the hazard names.

        Returns:
            HazardNames: HazardNames object.
        """
        if hazard_names_file and hazard_names_file.is_file():
            _names_df = pd.read_excel(hazard_names_file)
        else:
            _names_df = pd.DataFrame(data=None)
        return cls(names_df=_names_df)

    @classmethod
    def from_config(cls, analysis_config: AnalysisConfigWrapper) -> HazardNames:
        """
        Create a HazardNames object from an analysis configuration.

        Args:
            analysis_config (AnalysisConfigWrapper): Analysis configuration.

        Returns:
            HazardNames: HazardNames object.
        """
        if analysis_config.config_data.output_path:
            _hazard_file = analysis_config.config_data.output_path.joinpath(
                "hazard_names.xlsx"
            )
        else:
            _hazard_file = None
        return cls.from_file(_hazard_file)

    @property
    def names(self) -> list[str]:
        """
        Get the list of hazard names.

        Returns:
            list[str]: List of hazard names.
        """
        if self.names_df.empty:
            return []
        return self.names_df[FILE_NAME_KEY].tolist()

    def get_name(self, hazard: str) -> str:
        """
        Get the RA2CE name of a specific hazard.

        Args:
            hazard (str): Name of the hazard.

        Returns:
            str: RA2CE name of the hazard.
        """
        return self.names_df.loc[
            self.names_df[FILE_NAME_KEY] == hazard,
            RA2CE_NAME_KEY,
        ].values[0]
