from pathlib import Path

from tests.output_validator.file_validator_protocol import FileValidatorProtocol


class FeatherValidator(FileValidatorProtocol):
    @staticmethod
    def validate(reference_file: Path, result_file: Path) -> None:
        pass
