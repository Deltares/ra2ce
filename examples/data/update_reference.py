from pathlib import Path
from shutil import copy

from tests.output_validator.output_validator import OutputValidator


class UpdateReference:
    example_data_path: Path

    def __init__(self):
        self.example_data_path = Path(__file__).parent

    def update(self) -> None:
        for _example_data in self.example_data_path.iterdir():
            _example_reference = _example_data.joinpath("reference")
            if not _example_reference.is_dir():
                continue
            for _reference_file in OutputValidator._get_relative_paths(
                _example_reference
            ):
                _from = self.example_data_path.joinpath(_example_data, _reference_file)
                _to = self.example_data_path.joinpath(
                    _example_data, "reference", _reference_file
                )
                _to.parent.mkdir(parents=True, exist_ok=True)
                if _from.is_file():
                    copy(_from, _to)


UpdateReference().update()
