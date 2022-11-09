# -*- coding: utf-8 -*-
"""
Created on 21-9-2022

@author: F.C. de Groen, Deltares
"""

from tests.test_acceptance import run_from_cli


if __name__ == "__main__":
    run_from_cli(network_ini=r"C:\python\nepal\network.ini",
                 analysis_ini=r"C:\python\nepal\analyses.ini")

