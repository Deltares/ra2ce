from pathlib import Path

from ra2ce.analysis.damages.damage_functions.damage_function_road_type_lane import (
    DamageFunctionByRoadTypeByLane,
)
from ra2ce.analysis.damages.damage_functions.manual_damage_functions import (
    ManualDamageFunctions,
)
from ra2ce.common.io.readers.file_reader_protocol import FileReaderProtocol


class ManualDamageFunctionsReader(FileReaderProtocol):
    def read(self, file_path: Path) -> ManualDamageFunctions:
        def find_damage_functions(folder: Path) -> dict[str, Path]:
            return {
                subfolder.stem: subfolder
                for subfolder in folder.iterdir()
                if subfolder.is_dir()
            }

        _damage_functions: dict[str, DamageFunctionByRoadTypeByLane] = dict()
        for _name, _path in find_damage_functions(file_path).items():
            _damage_functions[_name] = DamageFunctionByRoadTypeByLane.from_input_folder(
                _name, _path
            )

        return ManualDamageFunctions(damage_functions=_damage_functions)
