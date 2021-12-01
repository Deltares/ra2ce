# -*- coding: utf-8 -*-
"""
Created on 6-8-2021

@author: F.C. de Groen, Deltares
"""

from ra2ce.ra2ce import main

if __name__ == '__main__':
    rootpath = r'c:\Python\ra2ce\data\KBN2_losses'
    main(rootpath + r"\network.ini", rootpath + r"\analyses.ini")
    # rootpath = r'c:\Python\ra2ce\data\8_test_shape_with_od_disruption'
    # main(rootpath + r"\network.ini", rootpath + r"\analyses.ini")
    # rootpath = r'c:\Python\ra2ce\data\1_test_network_shape'
    # main(rootpath + r"\network.ini", rootpath + r"\analyses.ini"