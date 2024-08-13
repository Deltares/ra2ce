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

import logging
from typing import Any, List

import numpy as np
import pandas as pd
from geopandas import GeoDataFrame


def clean_lane_data(lane_col: pd.Series) -> pd.Series:
    """
    Function that cleans up the lane data, to be used in case this contains unexpected values

    @author: Kees van Ginkel, Deltares

    Arguments:
        *lane_col* (Pandas Series) : The Panda series containing all lane information
                                    each value is still a string
    Returns:
        *new_lane_col* (Panda Series) : idem, but cleaned
                                    each value is already a float
    """

    # Todo: drawback of this approach is that you cannot easily see which lanes have the erratic lanedata,
    # The upside is that it is probably faster...
    # for index, cell in lane_col.iteritems():
    #    print(cell, type(cell))
    new_lane_col = lane_col.apply(lambda x: lane_cleaner(x))

    return new_lane_col


def lane_cleaner(cell: Any) -> float:
    """
    Helper function to clean an object with lane data and return it as a float

    @author: Kees van Ginkel, Deltares

    Arguments:
        *cell* (unknown format) : The cell with lane information to be cleaned

    Returns:
        *new* (float) : number of lanes or np.nan
    """
    if cell is None:
        return np.nan
    if isinstance(cell, int):
        return float(cell)
    if isinstance(cell, float):
        return cell
    if isinstance(cell, str):  # try to unpack the cell
        try:
            return float(cell)
        except Exception:
            logging.warning(
                "Lanedata {} could not be converted to float, if it is a list we will try to unpack".format(
                    cell
                )
            )

            def _get_max(list_values: List[str]) -> float:
                try:
                    _max_value = max(map(float, list_values))
                    logging.warning(
                        "Our best guess of the lane number is: {}".format(_max_value)
                    )
                except Exception:
                    logging.warning(
                        "Unexpected datatype, lane data removed {} {}".format(
                            cell, type(cell)
                        )
                    )
                    return np.nan
                return _max_value

            if ";" in cell:  # it looks some sort of a list
                return _get_max(cell.split(";"))
            elif "," in cell:  # it looks some sort of a list
                return _get_max(cell.split(","))
            return np.nan

    logging.warning(
        "Unexpected datatype, lane data removed {} {}".format(cell, type(cell))
    )
    return np.nan


def create_summary_statistics(gdf: GeoDataFrame) -> dict:
    """
    Return the mode (most frequent) #lanes of the available road types in the data

    @author: Kees van Ginkel, Deltares

    Arguments:
        *gdf* (GeoDataFrame) : needs the columns 'road_type' and 'lanes'

    Returns:
        *dictionary* (Dict) : keys = road types; values = lanes

    """
    # Todo: in the future we can make it more generic, so that we can easily get the mode/mean/whatever

    _grouped_lanes = gdf.groupby("road_type")["lanes"]
    _road_types, _lanes = list(zip(*((x[0], x[1].mode()) for x in _grouped_lanes)))
    _lanes_dict = {
        _road_type: _lanes[0] if not _lanes.empty else np.nan
        for _road_type, _lanes in zip(_road_types, _lanes)
    }

    # get a default value if any key of the dictionary is nan
    # (because the mode operation on the 'lanes' column for a road type results in an empty array)
    lanes_values = np.mean(
        list(_val for _val in _lanes_dict.values() if not np.isnan(_val))
    )
    # Round the mean to the nearest integer
    default_value = np.ceil(lanes_values)
    # Replace nan with the calculated average
    return {
        _road_type: _lanes if not np.isnan(_lanes) else default_value
        for _road_type, _lanes in _lanes_dict.items()
    }


def scale_damage_using_lanes(lane_scale_factors, df, cols_to_scale) -> pd.DataFrame:
    """
    Scale (max) damage or construction cost data using the lane data

    Arguments:
        *lane_scale_factors* (dict)  : output of damages_lookup.get_max_damages_OSD()
        *df* (pd.DataFrame)          : the data to scale, should have a col road_types, and a col lanes
        *cols_to_scale* (list)       : names of the columns to scale

    Returns:
        *df* (pd.Dataframe) : the scaled data
    """
    assert "road_type" in df.columns, "Road type data is missing"
    assert "lanes" in df.columns, "Lane number data is missing"
    df["road_type_scale_factors"] = df.apply(
        lambda x: lane_scale_factors[x.road_type][x.lanes], axis=1
    )

    for col in cols_to_scale:
        df[col] = df[col] * df["road_type_scale_factors"]

    df = df.drop(columns=["road_type_scale_factors"])

    return df
