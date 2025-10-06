from pathlib import Path
from typing import Protocol


class FileValidatorProtocol(Protocol):
    reference_file: Path
    result_file: Path

    def __init__(self, reference_file: Path, result_file: Path):
        """Initialize the validator with reference and result file paths."""

    def validate(self) -> None:
        """Validate the file content."""
