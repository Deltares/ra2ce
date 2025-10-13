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

from dataclasses import dataclass


@dataclass
class AdaptationOptionConfigData:
    """
    Reflects all possible settings that an adaptation option might contain.
    The id should be unique and is used to determine the location of the input and output files.
    This dataclass does not implement `AnalysisConfigDataProtocol` because it is not an analysis itself.
    """

    id: str = ""
    name: str = ""
    construction_cost: float = 0.0
    construction_interval: float = 1000.0
    maintenance_cost: float = 0.0
    maintenance_interval: float = 1000.0    
