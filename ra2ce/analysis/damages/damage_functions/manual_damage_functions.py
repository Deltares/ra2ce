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

from collections import defaultdict
from dataclasses import dataclass, field

from ra2ce.analysis.damages.damage_functions.damage_function_road_type_lane import (
    DamageFunctionByRoadTypeByLane,
)


@dataclass(kw_only=True)
class ManualDamageFunctions:
    """ "
    This class keeps an overview of the manual damage functions

    Default behaviour is to find, load and apply all available functions
    At 22 sept 2022: only implemented workflow for DamageFunction_by_RoadType_by_Lane
    """

    damage_functions: dict[str, DamageFunctionByRoadTypeByLane] = field(
        default_factory=lambda: defaultdict(DamageFunctionByRoadTypeByLane)
    )
