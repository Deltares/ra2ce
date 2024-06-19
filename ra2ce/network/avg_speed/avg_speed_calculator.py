import logging
from pathlib import Path

import networkx as nx

import ra2ce.network.networks_utils as nut
from ra2ce.network.avg_speed.avg_speed import AvgSpeed
from ra2ce.network.avg_speed.avg_speed_reader import AvgSpeedReader
from ra2ce.network.avg_speed.avg_speed_writer import AvgSpeedWriter


class AvgSpeedCalculator:
    graph: nx.Graph
    output_graph_dir: Path | None

    def __init__(self, graph: nx.Graph, output_graph_dir: Path | None) -> None:
        self.graph = graph
        self.output_graph_dir = output_graph_dir

    def calculate(self) -> AvgSpeed:
        if self.output_graph_dir:
            _avg_speed_path = self.output_graph_dir.joinpath("avg_speed.csv")
            if _avg_speed_path.is_file():
                return AvgSpeedReader().read(_avg_speed_path)

        logging.warning(
            "No valid file found with average speeds in %s, calculating and saving them instead.",
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
            _avg_speed = nut.calc_avg_speed(
                self.graph,
                "highway",
            )
            if self.output_graph_dir:
                AvgSpeedWriter().export(self.output_graph_dir, _avg_speed)
        else:
            logging.info(
                "No attributes found in the graph to estimate average speed per network segment."
            )
        return _avg_speed
