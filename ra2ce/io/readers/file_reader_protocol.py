from pathlib import Path
from typing import Any, Protocol


class FileReaderProtocol(Protocol):
    def read(self, file_path: Path) -> Any:
        pass
