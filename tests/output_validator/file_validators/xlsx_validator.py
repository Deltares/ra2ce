from pathlib import Path

from .file_validator_protocol import FileValidatorProtocol


class XlsxValidator(FileValidatorProtocol):
    @staticmethod
    def validate(reference_file: Path, result_file: Path) -> None:
        pass
