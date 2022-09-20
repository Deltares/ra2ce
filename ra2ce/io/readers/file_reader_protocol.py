from pathlib import Path
from typing import Any, Protocol


class FileReaderProtocol(Protocol):
    def read(self, ini_file: Path) -> Any:
        pass
