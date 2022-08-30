# -*- coding: utf-8 -*-
"""
Created on 30-8-2022

@author: F.C. de Groen, Deltares
"""

from abc import ABC

class AnalysisBase(ABC):
    network: Any = None # Should be type Network
    hazard: Any = None
    def __init__(self, network: Any):
        self.network = network

    def configure_analsyis(self):
        network.intialize()
        hazard.configure()

    def run_analysis(self):
        raise NotImplementedError("Should be implemented in lower class")

    def finalize(self):
        raise NotImplementedError("Should be implemented in lower class")

class AnalysisSimple(AnalysisBase):

    def run_analysis(self):
        #specific analysis for simple
        network.simple_configuration()...