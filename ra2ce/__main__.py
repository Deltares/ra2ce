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

# -*- coding: utf-8 -*-
import logging
from pathlib import Path
from typing import Optional

import click

from ra2ce.analysis.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.ra2ce_handler import Ra2ceHandler


### Below is the documentation for the commandline interface, see the CLICK-package.
@click.command()
@click.option(
    "--working_dir",
    default=None,
    help="Full path to the working directory, optionally containing the inifiles.",
)
@click.option(
    "--network_ini", default=None, help="Full path to or name of the network.ini file."
)
@click.option(
    "--analyses_ini",
    default=None,
    help="Full path to or name of the analyses.ini file.",
)
def run_analysis(
    working_dir: Optional[str], network_ini: Optional[str], analyses_ini: Optional[str]
) -> list[AnalysisResultWrapper]:
    _handler = get_handler(working_dir, network_ini, analyses_ini)
    _handler.configure()
    return _handler.run_analysis()


def get_handler(
    working_dir: Optional[str], network_ini: Optional[str], analyses_ini: Optional[str]
) -> Ra2ceHandler:
    def _as_path(
        working_dir: Optional[str], ini_file: Optional[str] = None
    ) -> Path | None:
        """
        Constructs a Path object from the given working directory and ini file.

        Args:
            working_dir (Optional[str]): Working directory where the ini files could be located.
            ini_file (Optional[str]): Name of or path to the ini file.

        Raises:
            FileNotFoundError: The working directory or ini file could not be found.

        Returns:
            Path | None: Path to the ini file (if provided and existing).
        """
        if working_dir:
            _working_dir = Path(working_dir)
            if not _working_dir.is_dir():
                raise FileNotFoundError(working_dir)
            if ini_file:
                _ini_file = _working_dir.joinpath(Path(ini_file).name)
                if not _ini_file.is_file():
                    return None
                return _ini_file
            return Path(_working_dir)
        if ini_file:
            _ini_file = Path(ini_file)
            if not _ini_file.is_file():
                raise FileNotFoundError(_ini_file)
            return _ini_file
        return None

    if network_ini:
        _network_ini = _as_path(working_dir, network_ini)
    elif working_dir:
        _network_ini = _as_path(working_dir, "network.ini")
    else:
        _network_ini = None

    if analyses_ini:
        _analysis_ini = _as_path(working_dir, analyses_ini)
    elif working_dir:
        _analysis_ini = _as_path(working_dir, "analyses.ini")
    else:
        _analysis_ini = None

    return Ra2ceHandler(_as_path(working_dir), _network_ini, _analysis_ini)


if __name__ == "__main__":
    try:
        run_analysis()
    except Exception as e_info:
        logging.error(str(e_info))
        raise
