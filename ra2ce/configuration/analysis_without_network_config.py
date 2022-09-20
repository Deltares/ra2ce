from pathlib import Path

import geopandas as gpd

from ra2ce.configuration.analysis_config_base import AnalysisConfigBase
from ra2ce.configuration.validators import AnalysisWithoutNetworkConfigValidator
from ra2ce.io.readers import GraphPickleReader


class AnalysisWithoutNetworkConfiguration(AnalysisConfigBase):
    def __init__(self, ini_file: Path, config_data: dict) -> None:
        if not ini_file.is_file():
            raise FileNotFoundError(ini_file)
        self.ini_file = ini_file
        self.config_data = config_data

    def _read_graphs_from_config(self) -> dict:
        _graphs = {}
        _pickle_reader = GraphPickleReader()
        _static_output_dir = self.config_data["static"] / "output_graph"
        for input_graph in ["base_graph", "origins_destinations_graph"]:
            # Load graphs
            _graphs[input_graph] = _pickle_reader.read(
                _static_output_dir / f"{input_graph}.p"
            )
            _graphs[input_graph + "_hazard"] = _pickle_reader.read(
                _static_output_dir / f"{input_graph}_hazard.p"
            )

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
        return (
            _file_is_valid
            and AnalysisWithoutNetworkConfigValidator(self.config_data).validate()
        )
