import logging
from pathlib import Path
from shutil import copyfile
from typing import List

from ra2ce.io.ra2ce_io_validator import _expected_values
from ra2ce.io.readers.file_reader_protocol import FileReaderProtocol
from ra2ce.io.readers.ini_file_reader import IniFileReader


class IniConfigurationReaderBase(FileReaderProtocol):
    """
    Generic BASE Ini Configuration Reader.
    It is meant to behave as an abstract class, the concrete classes should
    implement the read method from the FileReaderProtocol.
    """

    def _import_configuration(self, root_path: Path, config_path: Path) -> dict:
        # Read the configurations in network.ini and add the root path to the configuration dictionary.
        if not config_path.is_file():
            config_path = root_path / config_path
        _config = IniFileReader().read(config_path)
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
