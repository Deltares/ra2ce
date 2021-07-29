# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
"""


class DirectAnalyses:
    def __init__(self, config, network):
        self.shout = 'YESS'
        self.config = config
        self.gdf = network

    def execute(self):
        """Executes the direct analysis."""
        print(self.shout)
        return
