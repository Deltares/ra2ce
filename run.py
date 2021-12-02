# -*- coding: utf-8 -*-
"""
Created on 6-8-2021

@author: F.C. de Groen, Deltares
"""

from ra2ce.ra2ce import main

if __name__ == '__main__':

    rootpath = r'D:\ra2ceMaster\ra2ce\data\test'
    main(rootpath + r"\network.ini", rootpath + r"\analyses.ini")
