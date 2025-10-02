from pathlib import Path
from typing import Any

import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data_reader import (
    AnalysisConfigDataReader,
)
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.analysis_config_data.single_link_redundancy_config_data import (
    SingleLinkRedundancyConfigData,
)
from tests import acceptance_test_data


class TestAnalysisConfigReader:
    def test_initialize(self):
        # 1. Run test.
        _reader = AnalysisConfigDataReader()

        # 2. Verify expectations.
        assert isinstance(_reader, AnalysisConfigDataReader)

    @pytest.mark.parametrize(
        "ini_file",
        [
            pytest.param(None, id="None"),
            pytest.param("", id="Str"),
            pytest.param(Path("InvalidPath"), id="Non existent path."),
            pytest.param(Path("InvalidPath.ini"), id="Non existent path file."),
        ],
    )
    def test_read_without_ini_file_raises_error(self, ini_file: Any):
        # 1. Run test.
        with pytest.raises(ValueError) as exc_err:
            AnalysisConfigDataReader().read(ini_file)

        # 2. Verify expectations.
        assert str(exc_err.value) == "No analysis ini file 'Path' provided."

    def test_read_succeeds(self):
        # 1. Define test data
        _ini_file = acceptance_test_data.joinpath("analyses.ini")

        # 2. Run test
        _config = AnalysisConfigDataReader().read(_ini_file)

        # 3. Verify expectations
        assert isinstance(_config.input_path, Path)

    def test_get_analysis_sections(self):
        """
        Temporary test, to be better rewritten once all dataclasses are present.
        """
        # 1. Define test data
        _ini_file = acceptance_test_data.joinpath("analyses.ini")

        # 2. Run test
        _reader = AnalysisConfigDataReader()
        # Read everything so it gets correctly initialized.
        _ = _reader.read(_ini_file)
        _analyses_config_data = _reader._get_analysis_sections_with_new_dataclasses()

        # 3. Verify expectations
        assert isinstance(_analyses_config_data, list)
        
        _first_slr_cd = next(_sl_cd for _sl_cd in _analyses_config_data if isinstance(_sl_cd, SingleLinkRedundancyConfigData))
        assert _first_slr_cd.name == "single link redundancy test"
        assert _first_slr_cd.save_csv is True
        assert _first_slr_cd.save_gpkg is True
        assert _first_slr_cd.weighing == WeighingEnum.TIME
