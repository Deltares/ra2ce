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
    def _as_path(dirc: Optional[str], file: Optional[str] = None) -> Path | None:
        """Converts a directory and/or file to a Path to an existing directory or file."""
        if dirc:
            _dir = Path(dirc)
            if not _dir.is_dir():
                raise FileNotFoundError(dirc)
            if file:
                _file = _dir.joinpath(Path(file).name)
                if not _file.is_file():
                    return None
                return _file
            return Path(_dir)
        if file:
            _file = Path(file)
            if not _file.is_file():
                raise FileNotFoundError(_file)
            return _file
        return None

    def _construct_ini_path(
        working_dir: Optional[str], ini_file: Optional[str], default_name: str
    ) -> Path | None:
        """Constructs the Path to an ini file, based on the working directory and/or the ini file name."""
        if ini_file:
            return _as_path(working_dir, ini_file)
        if working_dir:
            return _as_path(working_dir, default_name)
        return None

    _network_ini = _construct_ini_path(working_dir, network_ini, "network.ini")
    _analysis_ini = _construct_ini_path(working_dir, analyses_ini, "analyses.ini")

    return Ra2ceHandler(_as_path(working_dir), _network_ini, _analysis_ini)


if __name__ == "__main__":
    try:
        run_analysis()
    except Exception as e_info:
        logging.error(str(e_info))
        raise
