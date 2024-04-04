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
    def _as_path(
        working_dir: Optional[str], ini_file: Optional[str] = None
    ) -> Path | None:
        if working_dir:
            _working_dir = Path(working_dir)
            if not _working_dir.is_dir():
                raise FileNotFoundError(working_dir)
            if ini_file:
                return _working_dir.joinpath(Path(ini_file).name)
            return Path(_working_dir)
        if ini_file:
            return Path(ini_file)
        return None

    if network_ini:
        _network_ini = _as_path(working_dir, network_ini)
        if not _network_ini.is_file():
            raise FileNotFoundError(_network_ini)
    elif working_dir:
        _network_ini = _as_path(working_dir, "network.ini")
    else:
        _network_ini = None

    if analyses_ini:
        _analysis_ini = _as_path(working_dir, analyses_ini)
        if not _analysis_ini.is_file():
            raise FileNotFoundError(_analysis_ini)
    elif working_dir:
        _analysis_ini = _as_path(working_dir, "analyses.ini")
    else:
        _analysis_ini = None

    _handler = Ra2ceHandler(_network_ini, _analysis_ini)
    _handler.configure()
    return _handler.run_analysis()


if __name__ == "__main__":
    try:
        run_analysis()
    except Exception as e_info:
        logging.error(str(e_info))
        raise
