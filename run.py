# -*- coding: utf-8 -*-
"""
Created on 6-8-2021

@author: F.C. de Groen, Deltares
"""

import click
from ra2ce.ra2ce import main


@click.command()
@click.option("--network_ini", default=None, help="Full path to the network.ini file.")
@click.option("--analyses_ini", default=None, help="Full path to the analyses.ini file.")
def cli(network_ini, analyses_ini):
    main(network_ini, analyses_ini)


if __name__ == "__main__":
    cli()
    # r"D:\ra2ceMaster\ra2ce\data\Nepal_shp_test\analyses.ini"
    # main(r"D:\ra2ceMaster\ra2ce\data\Nepal_shp_test\network.ini")