from pathlib import Path
from typing import Iterator

import pandas as pd
import pytest

from ra2ce.network.hazard.hazard_names import HazardNames
from tests import test_results


class TestHazardNames:

    def test_initialize(self):
        # 1. Define test data
        _data = [["a", 1], ["b", 2], ["c", 3]]
        _columns = ["name", "value"]
        _hazard_names_df = pd.DataFrame(_data, columns=_columns)
        _hazard_names = ["a", "b", "c"]

        # 2. Run test
        _hazard_names = HazardNames(_hazard_names_df, _hazard_names)

        # 3. Verify expectations
        assert _hazard_names.names_df.equals(_hazard_names_df)
        assert _hazard_names.names == _hazard_names.names

    def test_create_from_non_existing_file(self):
        # 1. Define test data
        _file = Path("non_existing_file.xlsx")

        # 2. Run test
        _hazard_names = HazardNames.from_file(_file)

        # 3. Verify expectations
        assert _hazard_names.names_df.empty
        assert _hazard_names.names == []

    @pytest.fixture(autouse=True)
    def hazard_names_file(self, request: pytest.FixtureRequest) -> Iterator[Path]:
        _output_path = test_results.joinpath(request.node.name)
        _output_path.mkdir(parents=True, exist_ok=True)
        _file = _output_path.joinpath("hazard_names.xlsx")
        _data = [["a", "A"], ["b", "B"], ["c", "C"]]
        _columns = ["File name", "RA2CE name"]
        _df = pd.DataFrame(_data, columns=_columns)
        _df.to_excel(_file, index=False)
        yield _file

        _output_path.unlink()

    def test_create_from_existing_file(self, hazard_names_file: Path):
        # 1. Define test data
        _file = hazard_names_file

        # 2. Run test
        _hazard_names = HazardNames.from_file(_file)

        # 3. Verify expectations
        assert _hazard_names.names_df.equals(pd.read_excel(_file))
        assert _hazard_names.names == ["a", "b", "c"]

    def test_get_name(self, hazard_names_file: Path):
        # 1. Define test data
        _file = hazard_names_file
        _hazard_names = HazardNames.from_file(_file)

        # 2. Run test
        _name = _hazard_names.get_name("a")

        # 3. Verify expectations
        assert _name == "A"
