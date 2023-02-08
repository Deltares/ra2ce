# -*- coding: utf-8 -*-
import logging
from pathlib import Path
from typing import Optional

import click

from ra2ce.ra2ce_handler import Ra2ceHandler


### Below is the documentation for the commandline interface, see the CLICK-package.
@click.command()
@click.option("--network_ini", default=None, help="Full path to the network.ini file.")
@click.option(
    "--analyses_ini", default=None, help="Full path to the analyses.ini file."
)
def run_analysis(network_ini: str = None, analyses_ini: str = None):
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
    _handler.run_analysis()


if __name__ == "__main__":
    try:
        run_analysis()
    except Exception as e_info:
        logging.error(str(e_info))
        raise
