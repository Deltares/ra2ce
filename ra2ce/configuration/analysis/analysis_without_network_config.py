from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from ra2ce.configuration import AnalysisConfigBase, AnalysisIniConfigData,NetworkConfig
from ra2ce.io.readers import GraphPickleReader


class AnalysisWithoutNetworkConfiguration(AnalysisConfigBase):
    def __init__(self) -> None:
        self.config_data = AnalysisIniConfigData()

    @classmethod
    def from_data(
        cls, ini_file: Path, config_data: AnalysisIniConfigData
    ) -> AnalysisWithoutNetworkConfiguration:
        """
        Initializes an `AnalysisWithoutNetworkConfiguration` with the given parameters.

        Args:
            ini_file (Path): Path to the ini file containing the analysis data.
            config_data (AnalysisIniConfigData): Ini data representation.

        Raises:
            FileNotFoundError: When the provided `ini file` cannot be found.

        Returns:
            AnalysisWithoutNetworkConfiguration: Initialized instance.
        """
        _new_analysis_config = cls()
        if not ini_file.is_file():
            raise FileNotFoundError(ini_file)
        _new_analysis_config.ini_file = ini_file
        _new_analysis_config.config_data = config_data
        _static_dir = config_data.get("static", None)
        if _static_dir and _static_dir.is_dir():
            config_data.files = NetworkConfig._get_existent_network_files(
                _static_dir / "output_graph"
            )
        _new_analysis_config.config_data['files'] = config_data.files
        return _new_analysis_config

    def _read_graphs_from_config(self) -> dict:
        _graphs = {}
        _pickle_reader = GraphPickleReader()
        _static_output_dir = self.config_data["static"] / "output_graph"

        # Load graphs
        # FIXME: why still read hazard as neccessary if analysis of single link redundancy can run wihtout hazard?
        for input_graph in ["base_graph", "origins_destinations_graph"]:
            filename = _static_output_dir / f"{input_graph}.p"
            if filename.is_file():
                _graphs[input_graph] = _pickle_reader.read(
                    filename
                )
            else:
                _graphs[input_graph] = None

            filename = _static_output_dir / f"{input_graph}_hazard.p"
            if filename.is_file():
                _graphs[input_graph + "_hazard"] = _pickle_reader.read(
                    filename
                )
            else:
                _graphs[input_graph + "_hazard"] = None

        # Load networks
        filename = _static_output_dir / f"base_network.feather"
        if filename.is_file():
            _graphs["base_network"] = gpd.read_feather(filename)
        else:
            _graphs["base_network"] = None

        filename = _static_output_dir / f"base_network_hazard.feather"
        if filename.is_file():
            _graphs["base_network_hazard"] = gpd.read_feather(filename)
        else:
            _graphs["base_network_hazard"] = None

        return _graphs

    def configure(self) -> None:
        self.graphs = self._read_graphs_from_config()
        self.initialize_output_dirs()

    def is_valid(self) -> bool:
        _file_is_valid = self.ini_file.is_file() and self.ini_file.suffix == ".ini"
        return _file_is_valid and self.config_data.is_valid()
