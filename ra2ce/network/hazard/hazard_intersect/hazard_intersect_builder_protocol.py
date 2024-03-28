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

from typing import Protocol

from geopandas import GeoDataFrame
from networkx import Graph


class HazardIntersectBuilderProtocol(Protocol):
    def get_intersection(
        self, hazard_overlay: GeoDataFrame | Graph
    ) -> GeoDataFrame | Graph:
        """
        Retrieves the resulting network from intersecting the hazard layer with a graph.

        Args:
            hazard_overlay (GeoDataFrame | Graph): Layer containing hazards.

        Returns:
            GeoDataFrame | Graph: Intersected graph with hazards.
        """
        pass
