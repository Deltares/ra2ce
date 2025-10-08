import ast
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from tests.output_validator.file_validators.file_validator_protocol import (
    FileValidatorProtocol,
)


@dataclass
class JsonValidator(FileValidatorProtocol):
    reference_file: Path
    result_file: Path

    def __post_init__(self) -> None:
        def _get_normalized_content(file_path: Path) -> pd.DataFrame:
            with open(file_path, "r", encoding="utf-8") as _file_path:
                return json.load(_file_path)

        _json_ref = _get_normalized_content(self.reference_file)
        _json_res = _get_normalized_content(self.result_file)

        if _json_ref == _json_res:
            return

        raise AssertionError(f"JSON file {self.result_file.name} deviates in content.")
