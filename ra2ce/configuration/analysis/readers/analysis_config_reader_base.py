from pathlib import Path

from ra2ce.configuration.readers.ini_config_reader_base import (
    IniConfigurationReaderBase,
)
from ra2ce.configuration.validators.ini_config_validator_base import (
    DirectAnalysisNameList,
    IndirectAnalysisNameList,
)
from ra2ce.io.readers.ini_file_reader import IniFileReader


class AnalysisConfigReaderBase(IniConfigurationReaderBase):
    def _convert_analysis_types(self, config: dict) -> dict:
        def set_analysis_values(config_type: str):
            if config_type in config:
                (config[config_type]).append(config[a])
            else:
                config[config_type] = [config[a]]

        analyses_names = [a for a in config.keys() if "analysis" in a]
        for a in analyses_names:
            if any(t in config[a]["analysis"] for t in DirectAnalysisNameList):
                set_analysis_values("direct")
            elif any(t in config[a]["analysis"] for t in IndirectAnalysisNameList):
                set_analysis_values("indirect")
            del config[a]

        return config

    def _import_configuration(self, root_path: Path, config_path: Path) -> dict:
        # Read the configurations in network.ini and add the root path to the configuration dictionary.
        if not config_path.is_file():
            config_path = root_path / config_path
        _config = IniFileReader().read(config_path)
        _config["project"]["name"] = config_path.parent.name
        _config["root_path"] = root_path

        # Set the output paths in the configuration Dict for ease of saving to those folders.
        _config["input"] = config_path.parent / "input"
        _config["static"] = config_path.parent / "static"
        # config["output"] = config["root_path"] / config["project"]["name"] / "output"
        return _config
