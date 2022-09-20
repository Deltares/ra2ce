import codecs
import logging
from ast import literal_eval
from configparser import ConfigParser
from pathlib import Path
from shutil import copyfile
from typing import List, Optional, Protocol

import numpy as np

from ra2ce.configuration.analysis_ini_configuration import (
    AnalysisIniConfigurationBase,
    AnalysisWithNetworkConfiguration,
    AnalysisWithoutNetworkConfiguration,
)
from ra2ce.configuration.ini_configuration_protocol import IniConfigurationProtocol
from ra2ce.configuration.network_ini_configuration import NetworkIniConfiguration
from ra2ce.io.ra2ce_io_validator import (
    DirectAnalysisNameList,
    IndirectAnalysisNameList,
    _expected_values,
)


class IniFileReaderProtocol(Protocol):
    def read(self, ini_file: Path) -> IniConfigurationProtocol:
        pass


class IniFileReader(IniFileReaderProtocol):
    def read(self, ini_file: Path) -> IniConfigurationProtocol:
        return self._parse_config(ini_file)

    def _parse_config(self, path: Path = None, opt_cli=None) -> dict:
        """Ajusted from HydroMT
        source: https://github.com/Deltares/hydromt/blob/af4e5d858b0ac0883719ca59e522053053c21b82/hydromt/cli/cli_utils.py"""
        opt = {}
        if path is not None and path.is_file():
            opt = self._configread(
                path, abs_path=False
            )  # Set from True to False 29-7-2021 by Frederique
            # make sure paths in config section are not abs paths
            if (
                "setup_config" in opt
            ):  # BELOW IS CURRENTLY NOT USED IN RA2CE BUT COULD BE GOOD FOR FUTURE LINKAGE WITH HYDROMT
                opt["setup_config"].update(self._configread(path).get("config", {}))
        elif path is not None:
            raise IOError(f"Config not found at {path}")
        if (
            opt_cli is not None
        ):  # BELOW IS CURRENTLY NOT USED IN RA2CE BUT COULD BE GOOD FOR FUTURE LINKAGE WITH HYDROMT
            for section in opt_cli:
                if not isinstance(opt_cli[section], dict):
                    raise ValueError(
                        f"No section found in --opt values: "
                        "use <section>.<option>=<value> notation."
                    )
                if section not in opt:
                    opt[section] = opt_cli[section]
                    continue
                for option, value in opt_cli[section].items():
                    opt[section].update({option: value})
        return opt

    def _configread(
        self,
        config_fn,
        encoding="utf-8",
        cf=None,
        defaults=dict(),
        noheader=False,
        abs_path=False,
    ):
        """read model configuration from file and parse to dictionary

        Ajusted from HydroMT
        source: https://github.com/Deltares/hydromt/blob/af4e5d858b0ac0883719ca59e522053053c21b82/hydromt/config.py"""
        if cf is None:
            cf = ConfigParser(allow_no_value=True, inline_comment_prefixes=[";", "#"])

        cf.optionxform = str  # preserve capital letter
        with codecs.open(config_fn, "r", encoding=encoding) as fp:
            cf.read_file(fp)
        root = Path(config_fn.stem)
        cfdict = defaults.copy()
        for section in cf.sections():
            if section not in cfdict:
                cfdict[section] = dict()  # init
            sdict = dict()
            for key, value in cf.items(section):
                try:
                    v = literal_eval(value)
                    assert not isinstance(v, tuple)  # prevent tuples from being parsed
                    value = v
                except Exception:
                    pass
                if abs_path:
                    if isinstance(value, str) and root.joinpath(value).exists():
                        value = root.joinpath(value).resolve()
                    elif isinstance(value, list) and np.all(
                        [root.joinpath(v).exists() for v in value]
                    ):
                        value = [root.joinpath(v).resolve() for v in value]
                sdict[key] = value
            cfdict[section].update(**sdict)
        if noheader and "dummy" in cfdict:
            cfdict = cfdict["dummy"]

        return cfdict


class IniConfigurationReaderBase(IniFileReaderProtocol):
    """
    Generic Ini Configuration Reader.
    Eventually it will be split into smaller readers for each type of IniConfiguration.
    """

    def _import_configuration(self, root_path: Path, config_path: Path) -> dict:
        # Read the configurations in network.ini and add the root path to the configuration dictionary.
        if not config_path.is_file():
            config_path = root_path / config_path
        _config = IniFileReader().read(path=config_path)
        _config["project"]["name"] = config_path.parts[-2]
        _config["root_path"] = root_path

        if "hazard" in _config:
            # TODO: This might only be relevant for NETWORK reader.
            if "hazard_field_name" in _config["hazard"]:
                if _config["hazard"]["hazard_field_name"]:
                    _config["hazard"]["hazard_field_name"] = _config["hazard"][
                        "hazard_field_name"
                    ].split(",")

        # Set the output paths in the configuration Dict for ease of saving to those folders.
        _config["input"] = _config["root_path"] / _config["project"]["name"] / "input"
        _config["static"] = _config["root_path"] / _config["project"]["name"] / "static"
        # config["output"] = config["root_path"] / config["project"]["name"] / "output"
        return _config

    def _copy_output_files(self, from_path: Path, config_data: dict) -> None:
        self._create_config_dir("output", config_data)
        # self._create_config_dir("static")
        try:
            copyfile(from_path, config_data["output"] / "{}.ini".format(from_path.stem))
        except FileNotFoundError as e:
            logging.warning(e)

    def _create_config_dir(self, dir_name: str, config_data: dict):
        _dir = config_data["root_path"] / config_data["project"]["name"] / dir_name
        if not _dir.exists():
            _dir.mkdir(parents=True)
        config_data[dir_name] = _dir

    def _parse_path_list(self, path_list: str) -> List[Path]:
        _list_paths = []
        for path_value in path_list.split(","):
            path_value = Path(path_value)
            if path_value.is_file():
                _list_paths.append(path_value)
                continue

            _project_name_dir = (
                self._config["root_path"] / self._config["project"]["name"]
            )
            abs_path = (
                _project_name_dir
                / "static"
                / self._input_dirs[self._config_property_name]
                / path_value
            )
            try:
                assert abs_path.is_file()
            except AssertionError:
                abs_path = (
                    _project_name_dir
                    / "input"
                    / self._input_dirs[self._config_property_name]
                    / path_value
                )

            self.list_paths.append(abs_path)

    def _update_path_values(self, config_data: dict) -> None:
        """
        TODO: Work in progress, for now it's happening during validation, which should not be the case.

        Args:
            config_data (dict): _description_
        """
        for key, value_dict in config_data.items():
            if not (dict == type(value_dict)):
                continue
            for k, v in value_dict.items():
                if "file" in _expected_values[key]:
                    self._config[key][k] = self._parse_path_list(v)


class AnalysisIniConfigurationReader(IniConfigurationReaderBase):
    def __init__(self, network_data: Optional[IniConfigurationProtocol]) -> None:
        self._network_data = network_data

    def _configure_analyses(self, config: dict) -> dict:
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

    def read(self, ini_file: Path) -> AnalysisIniConfigurationBase:
        if not ini_file:
            return None
        _root_path = AnalysisIniConfigurationBase.get_network_root_dir(ini_file)
        _config_data = self._import_configuration(_root_path, ini_file)
        # self._update_path_values(_config_data)
        _config_data = self._configure_analyses(_config_data)
        self._copy_output_files(ini_file, _config_data)
        if self._network_data:
            return AnalysisWithNetworkConfiguration(
                ini_file, _config_data, self._network_data
            )
        else:
            return AnalysisWithoutNetworkConfiguration(ini_file, _config_data)


class NetworkIniConfigurationReader(IniConfigurationReaderBase):
    def read(self, ini_file: Path) -> IniConfigurationProtocol:
        if not ini_file:
            return None
        _root_dir = NetworkIniConfiguration.get_network_root_dir(ini_file)
        _config_data = self._import_configuration(_root_dir, ini_file)
        # self._update_path_values(_config_data)
        self._copy_output_files(ini_file, _config_data)
        return NetworkIniConfiguration(ini_file, _config_data)
