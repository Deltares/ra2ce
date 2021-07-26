# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
"""

# Local modules
from utils import read_settings
from checks import input_validation
from graph import create_network
from analyses import analysis


def main():
    settings = read_settings()
    input_validation(settings)
    create_network()
    analysis()


if __name__ == '__main__':
    main()
