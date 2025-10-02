from pathlib import Path
from typing import Protocol


class FileValidatorProtocol(Protocol):
    @staticmethod
    def validate(reference_file: Path, result_file: Path) -> None:
        """Validate the file content."""
