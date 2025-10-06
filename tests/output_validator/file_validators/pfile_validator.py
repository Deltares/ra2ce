from pathlib import Path

from tests.output_validator.file_validators.file_validator_protocol import (
    FileValidatorProtocol,
)


class PfileValidator(FileValidatorProtocol):
    @staticmethod
    def validate(reference_file: Path, result_file: Path) -> None:
        pass
