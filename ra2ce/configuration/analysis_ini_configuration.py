from pathlib import Path
from typing import Dict

import geopandas as gpd

from ra2ce.configuration.ini_configuration_protocol import IniConfigurationProtocol
from ra2ce.configuration.network_ini_configuration import NetworkIniConfiguration
from ra2ce.io.readers import GraphPickleReader


class AnalysisIniConfigurationBase(IniConfigurationProtocol):
    ini_file: Path
    root_dir: Path
    config_data: Dict = None

    @staticmethod
    def get_network_root_dir(filepath: Path) -> Path:
        return filepath.parent.parent

    @property
    def root_dir(self) -> Path:
        return self.get_network_root_dir(self.ini_file)

    def initialize_output_dirs(self) -> None:
        """
        Initializes the required output directories for a Ra2ce analysis.
        """

        def _create_output_folders(analysis_type: str) -> None:
            # Create the output folders
            if not analysis_type in self.config_data.keys():
                return
            for a in self.config_data[analysis_type]:
                output_path = self.config_data["output"] / a["analysis"]
                output_path.mkdir(parents=True, exist_ok=True)

        _create_output_folders("direct")
        _create_output_folders("indirect")

    def is_valid(self) -> bool:
        return self.ini_file.is_file() and self.ini_file.suffix == ".ini"


class AnalysisWithNetworkConfiguration(AnalysisIniConfigurationBase):
    def __init__(
        self,
        ini_file: Path,
        analysis_data: dict,
        network_config: NetworkIniConfiguration,
    ) -> None:
        if not ini_file.is_file():
            raise FileNotFoundError(ini_file)
        self.ini_file = ini_file
        self._network_config = network_config
        self.config_data = analysis_data

    def configure(self) -> None:
        self.config_data["files"] = self._network_config.files
        self.config_data["network"] = self._network_config.config_data.get(
            "network", None
        )
        self.config_data["origins_destinations"] = self._network_config.config_data.get(
            "origins_destinations", None
        )

        # When Network is present the graphs are retrieved from the already configured object.
        self.graphs = self._network_config.graphs
        self.initialize_output_dirs()


class AnalysisWithoutNetworkConfiguration(AnalysisIniConfigurationBase):
    def __init__(self, ini_file: Path, config_data: dict) -> None:
        if not ini_file.is_file():
            raise FileNotFoundError(ini_file)
        self.ini_file = ini_file
        self.config_data = config_data

    def _update_with_network_configuration(self) -> dict:
        pass
        # try:
        #     _output_network_ini_file = self.config_data["output"] / "network.ini"
        #     assert _output_network_ini_file.is_file()

        #     _config_network = IniConfigurationReader().import_configuration(
        #         self.root_dir,
        #         config_path=_output_network_ini_file,
        #         check=False,
        #     )
        #     self.config_data.update(_config_network)
        #     self.config_data["origins_destinations"] = self.config_data["network"][
        #         "origins_destinations"
        #     ]
        # except FileNotFoundError:
        #     logging.error(
        #         f"The configuration file 'network.ini' is not found at {self.config_data['output'].joinpath('network.ini')}."
        #         f"Please make sure to name your network settings file 'network.ini'."
        #     )
        #     quit()

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
        self.config_data = self._update_with_network_configuration()
        self.initialize_output_dirs()
