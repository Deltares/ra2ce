from pathlib import Path
from typing import Any, Dict, List, Protocol


class ConfigurationProtocol(Protocol):
    ini_file: Path
    root_dir: Path
    config_data: Dict = None
    graphs: List[Any] = None

    def configure(self) -> None:
        raise NotImplementedError()

    def is_valid(self) -> bool:
        raise NotImplementedError()
