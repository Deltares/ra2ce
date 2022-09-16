# -*- coding: utf-8 -*-
import logging
from pathlib import Path

import click

from ra2ce.ra2ce import main


### Below is the documentation for the commandline interface, see the CLICK-package.
@click.command()
@click.option("--network_ini", required=True, help="Full path to the network.ini file.")
@click.option(
    "--analyses_ini", required=True, help="Full path to the analyses.ini file."
)
def cli(network_ini: str, analyses_ini: str):
    def _as_path(ini_file: str) -> Path:
        _ini = Path(ini_file)
        if not _ini.is_file():
            raise FileNotFoundError(_ini)
        return _ini

    _network_ini = _as_path(network_ini)
    _analysis_ini = _as_path(analyses_ini)
    main(_network_ini, _analysis_ini)


if __name__ == "__main__":
    try:
        cli()
    except Exception as e_info:
        logging.error(str(e_info))
