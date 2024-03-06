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
from typing import Protocol, runtime_checkable

from geopandas import GeoDataFrame
from networkx import MultiGraph


@runtime_checkable
class NetworkWrapperProtocol(Protocol):
    def get_network(self) -> tuple[MultiGraph, GeoDataFrame]:
        """
        Gets a network built within this wrapper instance. No arguments are accepted, the `__init__` method is meant to assign all required attributes for a wrapper.

        Returns:
            tuple[MultiGraph, GeoDataFrame]: Tuple of MultiGraph representing the graph and GeoDataFrame representing the network.
        """
        pass
