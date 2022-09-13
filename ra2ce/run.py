# -*- coding: utf-8 -*-
"""
Created on 6-8-2021

@author: F.C. de Groen, Deltares

This script (run.py) contains the command line interface configurations and is the starting point
for working with RA2CE, if you want to use RA2CE via the command line.
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
    cli()
