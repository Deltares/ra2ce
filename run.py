# -*- coding: utf-8 -*-
"""
Created on 6-8-2021

@author: F.C. de Groen, Deltares
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
    ### Todo: built check that tells you what went wrong
    # cli()
    main(r"D:\Python\ra2ce\data\91_OSdaMage_EAD\network.ini",r"D:\Python\ra2ce\data\91_OSdaMage_EAD\analysis.ini")
    #main(r"D:\Python\ra2ce\data\4_test_hazard_dominicana\network.ini",r"D:\Python\ra2ce\data\4_test_hazard_dominicana\analyses.ini")