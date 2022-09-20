from pathlib import Path
from typing import List

from ra2ce.validation.ra2ce_validator_protocol import Ra2ceIoValidator
from ra2ce.validation.validation_report import ValidationReport


class IniConfigPathValidator(Ra2ceIoValidator):
    def __init__(
        self,
        config_data: dict,
        config_property_name: str,
        path_values: str,
        input_dirs: List[Path],
    ) -> None:
        self.list_paths = []
        self._config = config_data
        self._config_property_name = config_property_name
        self._path_values = path_values
        self._input_dirs = input_dirs

    def validate(self) -> ValidationReport:
        # Check if the path is an absolute path or a file name that is placed in the right folder
        _report = ValidationReport()
        for path_value in self._path_values.split(","):
            path_value = Path(path_value)
            if path_value.is_file():
                self.list_paths.append(path_value)
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

            if not abs_path.is_file():
                _report.error(
                    "Wrong input to property [ {} ], file does not exist: {}".format(
                        self._config_property_name, abs_path
                    )
                )
                _report.error(
                    "If no file is needed, please insert value - None - for property - {} -".format(
                        self._config_property_name
                    )
                )
            else:
                self.list_paths.append(abs_path)

        return _report
