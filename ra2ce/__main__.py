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

from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.ra2ce_handler import Ra2ceHandler


### Below is the documentation for the commandline interface, see the CLICK-package.
@click.command()
@click.option("--network_ini", default=None, help="Full path to the network.ini file.")
@click.option(
    "--analyses_ini", default=None, help="Full path to the analyses.ini file."
)
def run_analysis(network_ini: str, analyses_ini: str) -> list[AnalysisResultWrapper]:
    def _as_path(ini_file: str) -> Optional[Path]:
        if not ini_file:
            return None

        _ini = Path(ini_file)
        if not _ini.is_file():
            raise FileNotFoundError(_ini)
        return _ini

    _network_ini = _as_path(network_ini)
    _analysis_ini = _as_path(analyses_ini)
    _handler = Ra2ceHandler(_network_ini, _analysis_ini)
    _handler.configure()
    return _handler.run_analysis()


if __name__ == "__main__":
    try:
        run_analysis()
    except Exception as e_info:
        logging.error(str(e_info))
        raise
