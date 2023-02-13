import logging
from typing import Any, List, Union

import numpy as np
import pandas as pd


def clean_lane_data(lane_col):
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
    """ "
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
        except:
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
                except:
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


def create_summary_statistics(gdf):
    """
    Return the mode (most frequent) #lanes of the available road types in the data

    @author: Kees van Ginkel, Deltares

    Arguments:
        *gdf* (GeoDataFrame) : needs the columns 'road_type' and 'lanes'

    Returns:
        *dictionary* (Dict) : keys = road types; values = lanes

    """
    # Todo: in the future we can make it more generic, so that we can easily get the mode/mean/whatever

    dictionary = dict(gdf.groupby("road_type")["lanes"].agg(pd.Series.mode))
    return dictionary


def scale_damage_using_lanes(lane_scale_factors, df, cols_to_scale) -> pd.DataFrame:
    """
    Scale (max) damage or construction cost data using the lane data

    Arguments:
        *lane_scale_factors* (dict)  : output of direct_lookup.get_max_damages_OSD()
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
