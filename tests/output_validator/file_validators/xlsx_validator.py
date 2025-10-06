from pathlib import Path

from tests.output_validator.file_validators.file_validator_protocol import (
    FileValidatorProtocol,
)


class XlsxValidator(FileValidatorProtocol):
    @staticmethod
    def validate(reference_file: Path, result_file: Path) -> None:
        # TODO: implement feather validation. Now only the existence of the file is checked.
        return
