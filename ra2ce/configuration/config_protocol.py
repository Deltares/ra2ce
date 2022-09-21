from __future__ import annotations

from pathlib import Path
from typing import Any, List, Protocol

from ra2ce.configuration.ini_config_protocol import IniConfigDataProtocol


class ConfigProtocol(Protocol):
    ini_file: Path
    root_dir: Path
    config_data: IniConfigDataProtocol = None
    graphs: List[Any] = None

    @classmethod
    def from_data(cls, ini_file: Path, config_data: IniConfigDataProtocol) -> ConfigProtocol:
        raise NotImplementedError()

    def configure(self) -> None:
        raise NotImplementedError()

    def is_valid(self) -> bool:
        raise NotImplementedError()
