# -*- coding: utf-8 -*-
"""
Created on 6-8-2021

@author: F.C. de Groen, Deltares
"""

from pathlib import Path
import click
from ra2ce.ra2ce import main


@click.command()
@click.option("--project", default=Path(__file__).resolve().parent / 'data' / 'test', help="Full path to the project folder of the RA2CE database.")
def cli(project):
    main(project + r"\network.ini", project + r"\analyses.ini")


if __name__ == "__main__":
    cli()
