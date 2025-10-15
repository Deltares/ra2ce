from pathlib import Path
from re import S

import pytest

from ra2ce.analysis.analysis_config_data import LossesConfigDataTypes
from ra2ce.analysis.analysis_config_data.adaptation_config_data import (
    AdaptationConfigData,
)
from ra2ce.analysis.analysis_config_data.adaptation_option_config_data import (
    AdaptationOptionConfigData,
)
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    ProjectSection,
)
from ra2ce.analysis.analysis_config_data.base_link_losses_config_data import (
    SingleLinkLossesConfigData,
)
from ra2ce.analysis.analysis_config_data.damages_config_data import DamagesConfigData
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_enum import AnalysisEnum
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.losses.single_link_losses import SingleLinkLosses
from tests import test_results


class TestAnalysisConfigData:
    def test_initialize(self):
        _config_data = AnalysisConfigData()
        # At this moment it's not really mapped as a FOM.
        assert isinstance(_config_data, dict)
        assert isinstance(_config_data, AnalysisConfigData)

    @pytest.fixture
    def valid_config(self) -> AnalysisConfigData:
        _config = AnalysisConfigData(project=ProjectSection())
        for _losses_config in LossesConfigDataTypes:
            _config.analyses.append(
                _losses_config(name=_losses_config.__name__.lower())
            )
        
        _config.analyses.append(
            DamagesConfigData(name="damages_analysis")
        )
        _adaptation_config = AdaptationConfigData(name="adaptation_analysis")
        _adaptation_config.adaptation_options = [
            AdaptationOptionConfigData(id="AO0"),
            AdaptationOptionConfigData(id="AO1"),
            AdaptationOptionConfigData(id="AO2"),
        ]
        _config.analyses.append(_adaptation_config)
        yield _config

    def test_losses(self, valid_config: AnalysisConfigData):
        # 1./2. Define test data/Run test
        _losses = [
            type(_config) for _config in valid_config.losses_list
        ]

        # 3. Verify expectations
        assert all(item in _losses for item in LossesConfigDataTypes)

    def test_damages(self, valid_config: AnalysisConfigData):
        # 1./2. Define test data/Run test
        _damages = [
            type(_config) for _config in valid_config.damages_list
        ]

        # 3. Verify expectations
        assert len(_damages) == 1
        assert all(_damage_type == DamagesConfigData for _damage_type in _damages)

    def test_adaptation(self, valid_config: AnalysisConfigData):
        # 1./2. Define test data/Run test
        _adaptation = valid_config.adaptation

        # 3. Verify expectations
        assert isinstance(_adaptation, AdaptationConfigData)
        assert all(
            isinstance(_item, AdaptationOptionConfigData)
            for _item in _adaptation.adaptation_options
        )

    def test_get_data_output(self):
        # 1. Define test data
        _test_ini = test_results / "non_existing.ini"
        _expected_value = test_results / "output"

        # 2. Run test
        _return_value = AnalysisConfigData.get_data_output(_test_ini)

        # 3. Verify expectations.
        assert _return_value == _expected_value

    @pytest.mark.parametrize(
        "analysis_type",
        (
            *LossesConfigDataTypes,
            DamagesConfigData,
            AdaptationConfigData,
        ),
    )
    def test_get_analysis_returns_analysis_config(
        self,
        valid_config: AnalysisConfigData,
        analysis_type: AnalysisLossesEnum | AnalysisDamagesEnum | AnalysisEnum,
    ):
        # 1./2. Define test data/Run test
        _result = valid_config.get_analysis(analysis_type)

        # 3. Verify expectations
        assert isinstance(_result, analysis_type)

    def test_reroot_analysis_config(self, valid_config: AnalysisConfigData):
        # 1. Define test data
        _analysis_type = SingleLinkLossesConfigData
        _analysis = valid_config.get_analysis(_analysis_type)
        _file = Path("old_root/a_dir/file.ext")
        valid_config.root_path = _file.parent
        _analysis.resilience_curves_file = _file
        _root_path = Path("new_root/another_dir")
        _expected_path = _root_path.joinpath(AnalysisLossesEnum.SINGLE_LINK_LOSSES.config_value, _file.name)

        # 2. Run test
        _result = valid_config.reroot_analysis_config(_analysis_type, _root_path)

        # 3. Verify expectations
        _result_analysis = _result.get_analysis(_analysis_type)
        assert _result_analysis.resilience_curves_file == _expected_path
