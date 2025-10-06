from pathlib import Path

from tests.output_validator.file_validators.file_validator_protocol import (
    FileValidatorProtocol,
)


class PfileValidator(FileValidatorProtocol):
    reference_file: Path
    result_file: Path

    def __init__(self, reference_file: Path, result_file: Path):
        self.reference_file = reference_file
        self.result_file = result_file

    def validate(self) -> None:
        # TODO: implement feather validation. Now only the existence of the file is checked.
        return
