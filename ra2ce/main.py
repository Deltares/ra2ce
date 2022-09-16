# -*- coding: utf-8 -*-
"""
Created on 6-8-2021

@author: F.C. de Groen, Deltares

This script (run.py) contains the command line interface configurations and is the starting point
for working with RA2CE, if you want to use RA2CE via the command line.
"""

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
        if not ini_file:
            raise ValueError(f"Not a valid path given: {ini_file}")
        _ini = Path(ini_file)
        if not _ini.is_file():
            raise FileNotFoundError(_ini)

    _network_ini = _as_path(network_ini)
    _analysis_ini = _as_path(analyses_ini)
    main(_network_ini, _analysis_ini)


if __name__ == "__main__":
    cli()
