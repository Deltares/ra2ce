import shutil
from pathlib import Path

import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionDamages,
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper
from tests import test_data, test_results


class TestAnalysisConfigWrapper:
    def test_from_data_no_file_raises(self):
        with pytest.raises(FileNotFoundError):
            AnalysisConfigWrapper.from_data_with_network(Path("not_a_file"), None, None)

    def test_initialize(self):
        _config = AnalysisConfigWrapper()
        assert isinstance(_config, AnalysisConfigWrapper)
        assert isinstance(_config.config_data, AnalysisConfigData)

    @pytest.fixture(autouse=False)
    def valid_analysis_ini(self) -> Path:
        _ini_file = test_data / "acceptance_test_data" / "analyses.ini"
        assert _ini_file.exists()
        return _ini_file

    def test_from_data_network_not_provided(self, valid_analysis_ini: Path):
        # 1. Define test data.
        _config_data = AnalysisConfigData()

        # 2. Run test.
        with pytest.raises(ValueError):
            AnalysisConfigWrapper.from_data_with_network(
                valid_analysis_ini, _config_data, None
            )

    def test_from_data_with_network(self, valid_analysis_ini: Path):
        # 1. Define test data.
        _config_data = AnalysisConfigData()
        _network_config = NetworkConfigWrapper()

        # 2. Run test.
        _config = AnalysisConfigWrapper.from_data_with_network(
            valid_analysis_ini, _config_data, _network_config
        )

        # 3. Verify final expectations.
        assert isinstance(_config, AnalysisConfigWrapper)
        assert _config.config_data == _config_data
        assert _config.ini_file == valid_analysis_ini

    def test_configure(self, valid_analysis_ini: Path):
        # 1. Define test data.
        _config_data = AnalysisConfigData()
        _network_config = NetworkConfigWrapper()
        _config = AnalysisConfigWrapper.from_data_with_network(
            valid_analysis_ini, _config_data, _network_config
        )

        # 2. Run test.
        _config.configure()

    def test_initialize_output_dirs_with_valid_data(
        self, request: pytest.FixtureRequest
    ):
        # 1. Define test data
        _analysis = AnalysisConfigWrapper()
        _output_dir = test_results / request.node.name
        _analysis.config_data = AnalysisConfigData(output_path=_output_dir)
        _analysis.config_data.analyses = [
            AnalysisSectionDamages(analysis=AnalysisDamagesEnum.EFFECTIVENESS_MEASURES),
            AnalysisSectionLosses(analysis=AnalysisLossesEnum.SINGLE_LINK_REDUNDANCY),
        ]
        if _output_dir.exists():
            shutil.rmtree(_output_dir)

        # 2. Run test
        _analysis.initialize_output_dirs()

        # 3. Verify expectations.
        assert _output_dir.exists()
        assert _output_dir.joinpath("effectiveness_measures").exists()
        assert _output_dir.joinpath("single_link_redundancy").exists()

    def test_analysis_config_wrapper_valid_without_ini_file(self):
        # 1. Define test data
        _analysis_wrapper = AnalysisConfigWrapper()
        _analysis_wrapper.config_data = AnalysisConfigData()
        _analysis_wrapper.config_data.analyses.append(
            AnalysisSectionDamages(
                analysis=AnalysisDamagesEnum.DIRECT_DAMAGE,
                event_type=EventTypeEnum.EVENT,
                damage_curve=DamageCurveEnum.HZ,
            )
        )
        _analysis_wrapper.ini_file = None

        # 2. Run test.
        _result = _analysis_wrapper.is_valid()

        # 3. Verify expectations.
        assert _result is True
