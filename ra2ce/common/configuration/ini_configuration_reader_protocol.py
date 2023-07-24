from typing import Protocol, runtime_checkable

from ra2ce.configuration.config_protocol import ConfigProtocol
from ra2ce.common.io.readers.file_reader_protocol import FileReaderProtocol
from pathlib import Path


@runtime_checkable
class IniConfigurationReaderProtocol(FileReaderProtocol, Protocol):  # pragma: no cover
    def read(self, ini_file: Path) -> ConfigProtocol:
        """
        Reads the given `*.ini` file and if possible converts it into a `ConfigProtocol` object.

        Args:
            ini_file (Path): Ini file to be mapped into a `ConfigProtocol`.

        Returns:
            ConfigProtocol: Resulting mapped object from the configuration data in the given file.
        """
        pass
