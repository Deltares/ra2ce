"""
                    GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

    Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023 Stichting Deltares

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


from pathlib import Path

import geopandas as gpd
import numpy as np


def from_shapefile_to_poly(shapefile: Path, out_path: Path, outname: str = ""):

    """
    This function will create the .poly files from an input shapefile.
    If the shapefile contains multiple polygons, this function creates a seperate .polygon file for each region
    .poly files can then be used to extract data from the openstreetmap files.

    This function is adapted from the OSMPoly function in QGIS, and Elco Koks GMTRA model.
    This code is maintained on a GitHub repository: github.com/keesvanginkel/OSdaMage

    Arguments:
        *shapefile* (string/Pathlib Path) : path to the shapefile
        *out_path* (string/Pathlib Path): path to the directory where the .poly files should be written
        *outname* (string) : optional prefix to add to outfile name

    Returns:
        .poly file for each region, in a new dir in the working directory (in the CRS of te input file)
    """
    shp_file_gdf = gpd.read_file(str(shapefile))

    num = 0
    # iterate over the seperate polygons in the shapefile
    for f in shp_file_gdf.iterrows():
        f = f[1]
        num = num + 1
        geom = f.geometry

        try:
            # this will create a list of the different subpolygons
            if geom.geom_type == "MultiPolygon":
                polygons = geom

            # the list will be length 1 if it is just one polygon
            elif geom.geom_type == "Polygon":
                polygons = [geom]

            # define the name of the output file
            id_name = str(f.name)

            # start writing the .poly file
            _poly_filename = out_path / (outname + id_name + ".poly")
            with open(_poly_filename, "w") as _poly_file:
                _poly_file.write(id_name + "\n")
                i = 0

                # loop over the different polygons, get their exterior and write the
                # coordinates of the ring to the .poly file
                for polygon in polygons:
                    polygon = np.array(polygon.exterior)

                    j = 0
                    _poly_file.write(str(i) + "\n")

                    for ring in polygon:
                        j = j + 1
                        _poly_file.write(
                            "    " + str(ring[0]) + "     " + str(ring[1]) + "\n"
                        )

                    i = i + 1
                    # close the ring of one subpolygon if done
                    _poly_file.write("END" + "\n")

                # close the file when done
                _poly_file.write("END" + "\n")
        except Exception as e:
            print("Exception {}".format(e))
