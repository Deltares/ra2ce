# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
"""


class Network:
    def __init__(self):
        self.something = 'bla'

    def network_shp(self):
        """Creates a network from a shapefile."""
        return

    def network_osm_pbf(self):
        """Creates a network from an OSM PBF file."""
        return

    def network_osm_download(self):
        """Creates a network from a polygon by downloading via the OSM API in the extent of the polygon."""
        return

    def add_od_nodes(self):
        """Adds origins and destinations nodes from shapefiles to the graph."""
        return

    def create(self):
        """Function with the logic to call the right analyses."""
        return


class Hazard:
    def __init__(self):
        self.something = 'bla'

    def overlay_hazard_raster(self):
        """Overlays the hazard raster over the road segments."""
        return

    def overlay_hazard_shp(self):
        """Overlays the hazard shapefile over the road segments."""
        return

    def join_hazard_table(self):
        """Joins a table with IDs and hazard information with the road segments with corresponding IDs."""
        return
