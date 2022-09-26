from pathlib import Path
from typing import Any, Protocol


class FileReaderProtocol(Protocol):
    def read(self, file_path: Path) -> Any:
        """
        Reads from a given file and converts the data into `Any` type.

        Args:
            file_path (Path): Path to a file containing data to be read.

        Returns:
            Any: Object mapped from the data in the file.
        """
        pass
