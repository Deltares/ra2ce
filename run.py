# -*- coding: utf-8 -*-
"""
Created on 6-8-2021

@author: F.C. de Groen, Deltares

TODO: explain
run.py is command line interface (starting point for working with RA2CE if you're working on the command line)
"""

import click
from ra2ce.ra2ce import main


### Below is the documentation for the commandline interface, see the CLICK-package.
@click.command()
@click.option("--network_ini", default=None, help="Full path to the network.ini file.")
@click.option("--analyses_ini", default=None, help="Full path to the analyses.ini file.")
def cli(network_ini, analyses_ini):
    main(network_ini, analyses_ini)


if __name__ == "__main__":
    # main(r"D:\ra2ceMaster\ra2ce\data\Nepal_shp_test\network.ini")
