# -*- coding: utf-8 -*-
"""
Created on 30-8-2022

@author: F.C. de Groen, Deltares
"""

class TestAcceptance:

    def test_given_when(self):
        from ra2ce.ra2ce import main
        main(r"d:\ra2ceMaster\ra2ce\tests\local_data\network.ini",
             r"d:\ra2ceMaster\ra2ce\tests\local_data\analyses.ini")
