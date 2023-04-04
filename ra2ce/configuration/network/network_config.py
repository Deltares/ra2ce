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


from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional

from geopandas import gpd

from ra2ce.configuration.config_protocol import ConfigProtocol
from ra2ce.configuration.network.network_ini_config_data import NetworkIniConfigData
from ra2ce.graph.hazard import Hazard
from ra2ce.graph.networks import Network
from ra2ce.io.readers import GraphPickleReader


def network_handler(config: dict, files: dict) -> Optional[dict]:
    try:
        network = Network(config, files)
        graphs = network.create()
        return graphs

    except BaseException as e:
        logging.exception(
            f"RA2CE crashed. Check the logfile for the Traceback message: {e}"
        )
        raise e


def hazard_handler(config: dict, graphs: dict, files: dict) -> Optional[dict]:
    if config["hazard"]["hazard_map"] is not None:
        # There is a hazard map or multiple hazard maps that should be intersected with the graph.
        hazard = Hazard(config, graphs, files)
        graphs = hazard.create()
        return graphs
    else:
        return None


class NetworkConfig(ConfigProtocol):
    files: Dict[str, Path] = {}
    config_data: NetworkIniConfigData

    def __init__(self) -> None:
        self.config_data = NetworkIniConfigData()

    @classmethod
    def from_data(
        cls, ini_file: Path, config_data: NetworkIniConfigData
    ) -> NetworkConfig:
        """
        Initializes a `NetworkConfig` with the given parameters.

        Args:
            ini_file (Path): Path to the ini file containing the analysis data.
            config_data (NetworkIniConfigData): Ini data representation.

        Returns:
            NetworkConfig: Initialized instance.
        """
        _new_network_config = cls()
        _new_network_config.ini_file = ini_file
        _new_network_config.config_data = config_data
        _static_dir = config_data.get("static", None)
        if _static_dir and _static_dir.is_dir():
            _new_network_config.files = _new_network_config._get_existent_network_files(
                _static_dir / "output_graph"
            )
        else:
            logging.error(f"Static dir not found. Value provided: {_static_dir}")
        return _new_network_config

    @staticmethod
    def get_network_root_dir(filepath: Path) -> Path:
        return filepath.parent.parent

    @staticmethod
    def get_data_output(ini_file: Path) -> Optional[Path]:
        return ini_file.parent / "output"

    @staticmethod
    def _get_existent_network_files(output_graph_dir: Path) -> dict:
        """Checks if file of graph exist in network folder and adds filename to the files dict"""
        _network_filenames = [
            "base_graph.p",
            "base_network.feather",
            "origins_destinations_graph.p",
            "base_graph_hazard.p",
            "origins_destinations_graph_hazard.p",
            "base_network_hazard.feather",
        ]

        def _get_file_entry(expected_file: Path) -> Optional[Path]:
            _value = None
            if expected_file and expected_file.is_file():
                _value = expected_file
                logging.info(f"Existing graph/network found: {expected_file}.")
            return _value

        return {
            _ep.stem: _get_file_entry(_ep)
            for _ep in map(lambda x: output_graph_dir / x, _network_filenames)
        }

    @property
    def root_dir(self) -> Path:
        return self.get_network_root_dir(self.ini_file)

    @staticmethod
    def read_graphs_from_config(static_output_dir: Path) -> dict:
        _graphs = {}
        _pickle_reader = GraphPickleReader()
        if not static_output_dir.exists():
            raise ValueError("Path does not exist: {}".format(static_output_dir))
        # Load graphs
        # FIXME: why still read hazard as neccessary if analysis of single link redundancy can run wihtout hazard?
        for input_graph in ["base_graph", "origins_destinations_graph"]:
            filename = static_output_dir / f"{input_graph}.p"
            if filename.is_file():
                _graphs[input_graph] = _pickle_reader.read(filename)
            else:
                _graphs[input_graph] = None

            filename = static_output_dir / f"{input_graph}_hazard.p"
            if filename.is_file():
                _graphs[input_graph + "_hazard"] = _pickle_reader.read(filename)
            else:
                _graphs[input_graph + "_hazard"] = None

        # Load networks
        filename = static_output_dir / "base_network.feather"
        if filename.is_file():
            _graphs["base_network"] = gpd.read_feather(filename)
        else:
            _graphs["base_network"] = None

        filename = static_output_dir / "base_network_hazard.feather"
        if filename.is_file():
            _graphs["base_network_hazard"] = gpd.read_feather(filename)
        else:
            _graphs["base_network_hazard"] = None

        return _graphs

    def configure_network(self) -> None:
        # Call Network Handler (to rework)
        self.graphs = network_handler(self.config_data, self.files)

    def configure_hazard(self) -> None:
        # Call Hazard Handler (to rework)
        if not self.graphs:
            self.graphs = self.read_graphs_from_config(
                self.config_data["static"] / "output_graph"
            )
        self.graphs = hazard_handler(self.config_data, self.graphs, self.files)

    def is_valid(self) -> bool:
        _file_is_valid = self.ini_file.is_file() and self.ini_file.suffix == ".ini"
        return _file_is_valid and self.config_data.is_valid()
