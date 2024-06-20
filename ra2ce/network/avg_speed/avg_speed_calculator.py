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
from pathlib import Path
from re import split
from statistics import mean

import networkx as nx

import ra2ce.network.networks_utils as nut
from ra2ce.network.avg_speed.avg_speed import AvgSpeed
from ra2ce.network.avg_speed.avg_speed_reader import AvgSpeedReader
from ra2ce.network.avg_speed.avg_speed_writer import AvgSpeedWriter
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


class AvgSpeedCalculator:
    """
    Class to calculate the average speed of a road network based on the maximum speed of the roads.
    """

    graph: nx.Graph
    output_graph_dir: Path | None
    avg_speed: AvgSpeed

    def __init__(self, graph: nx.Graph, output_graph_dir: Path | None) -> None:
        self.graph = graph
        self.output_graph_dir = output_graph_dir
        self.avg_speed = None

    @staticmethod
    def parse_speed(speed_input: str | list[str]) -> float:
        """
        Parse the average speed from the input string(s).

        Args:
            speed_input (str | list[str]): (List of) string(s) with the speed(s).
                Can have different formats, e.g. "50 mph", "50", "50;60", "50-60", "50|60".

        Returns:
            float: Average speed of the input string(s).
                0.0 is returned if the input is empty or can't be parsed correctly.
        """
        if not speed_input:
            return 0.0
        if isinstance(speed_input, list):
            return mean(map(AvgSpeedCalculator.parse_speed, speed_input))
        if " mph" in speed_input:
            return float(speed_input.split(" mph")[0]) * 1.609344
        if any(c.isalpha() for c in speed_input):
            return 0.0
        # Split on the different separators (";" or "-" or "|")
        # and take the mean of the results (if any).
        return mean(float(x) for x in split(r";|-|\|", speed_input) if x.isnumeric())

    def _get_avg_speed(
        self,
        road_type_col_name: str,
    ) -> AvgSpeed:
        def get_main_speed(link_type: RoadTypeEnum) -> float:
            _base_rt = RoadTypeEnum.get_enum(str(link_type).split("_link")[0])
            if _base_rt in _avg_speed.road_types:
                return _avg_speed.get_avg_speed(_base_rt)
            return 0.0

        def get_uncombined_speed(combined_types: list[RoadTypeEnum]) -> float:
            for _rt in combined_types:
                if _rt in _avg_speed.road_types:
                    return _avg_speed.get_avg_speed(_rt)
            return 0.0

        _avg_speed = AvgSpeed()

        for _rt in list(
            set(
                str(edata[road_type_col_name])
                for _, _, edata in self.graph.edges.data()
            )
        ):
            edge_data = [
                (self.parse_speed(edata["maxspeed"]), edata["length"])
                for _, _, edata in self.graph.edges.data()
                if (edata[road_type_col_name] == _rt) & ("maxspeed" in edata)
            ]
            if not edge_data:
                _avg_speed.set_avg_speed(_rt, 0.0)
            else:
                # Calculate weighted average speed
                edge_speed, edge_length = zip(*edge_data)
                _avg_speed.set_avg_speed(
                    _rt,
                    sum(s * l for s, l in zip(edge_speed, edge_length))
                    / sum(edge_length),
                )

        # For all types without an average speed, take one that is most likely.
        _zero_rts = [
            _rt for _rt in _avg_speed.road_types if _avg_speed.get_avg_speed(_rt) == 0
        ]
        if _zero_rts:
            logging.info(
                "Not all of the edges contain a 'maxspeed' attribute. RA2CE will guess the right average maximum "
                "speed per road type that does not contain a 'maxspeed' attribute. Please check the average speed CSV to ensure correct speeds."
            )
            for _rt in _zero_rts:
                if isinstance(_rt, list):
                    # Try to get the speed from the uncombined road types in the list.
                    _uncombined_speed = get_uncombined_speed(_rt)
                    if _uncombined_speed:
                        _avg_speed.set_avg_speed(_rt, _uncombined_speed)
                        continue
                # For the links take the one of the same type of the main roads.
                if "_link" in str(_rt):
                    _main_speed = get_main_speed(_rt)
                    if _main_speed:
                        _avg_speed.set_avg_speed(_rt, _main_speed)
                        continue
                _avg_speed.set_avg_speed(_rt, _avg_speed.default_speed)
                logging.warning(
                    "Default speed have been assigned to road type %s. Please check the average speed CSV, "
                    "enter the right average speed for this road type and run RA2CE again.",
                    _rt,
                )

        return _avg_speed

    def calculate(self) -> AvgSpeed:
        """
        Calculates the average speed from OSM roads, per road type.
        If the average speed is already calculated and saved in a CSV, it will be read from there.
        After calculation it will be saved in a CSV file in the output_graph_dir.

        Args: None

        Returns:
            AvgSpeed: Object with the average speeds per road type
        """
        if self.output_graph_dir:
            _avg_speed_path = self.output_graph_dir.joinpath("avg_speed.csv")
            if _avg_speed_path.is_file():
                return AvgSpeedReader().read(_avg_speed_path)

            logging.warning(
                "No valid file found with average speeds %s, calculating and saving them instead.",
                _avg_speed_path,
            )

        _length_array, _maxspeed_array = list(
            zip(
                *(
                    ("length" in e, "maxspeed" in e)
                    for _, _, e in self.graph.edges.data()
                )
            )
        )
        if all(_length_array) and any(_maxspeed_array):
            # Add time weighing - Define and assign average speeds; or take the average speed from an existing CSV
            _avg_speed = self._get_avg_speed("highway")
            if self.output_graph_dir:
                AvgSpeedWriter().export(
                    self.output_graph_dir.joinpath("avg_speed.csv"), _avg_speed
                )
        else:
            _avg_speed = AvgSpeed()
            logging.info(
                "No attributes found in the graph to estimate average speed per network segment."
            )

        self.avg_speed = _avg_speed
        return _avg_speed

    def assign(self) -> nx.Graph:
        """
        Assigns the average speed and time to roads in an existing (OSM) graph.
        If not already calculated, the average speed will be calculated first.

        Args: None

        Returns:
            graph (NetworkX graph): NetworkX graph with an additional attribute 'avgspeed' and 'time'
        """

        if not self.avg_speed:
            self.avg_speed = self.calculate()

        # calculate the average maximum speed per edge and assign the ones that don't have a value
        for u, v, k, edata in self.graph.edges.data(keys=True):
            _rt = edata.get("highway", None)
            _length = edata.get("length", None)  # m
            _speed = self.parse_speed(edata.get("maxspeed", None))
            if not _length:
                _length = nut.line_length(edata["geometry"], self.graph.graph["crs"])
                self.graph.edges[u, v, k]["length"] = _length
            if not _speed:
                _speed = self.avg_speed.get_avg_speed(_rt)
            self.graph.edges[u, v, k]["avgspeed"] = max(
                round(_speed, 0), 1
            )  # km/h (at least 1)
            self.graph.edges[u, v, k]["time"] = round(_length * 1e-3 / _speed, 3)  # h

        return self.graph
