from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class FileValidatorProtocol(Protocol):
    reference_file: Path
    result_file: Path
