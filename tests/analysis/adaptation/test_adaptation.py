from pathlib import Path
from typing import Iterator

import pytest
from geopandas import GeoDataFrame

from ra2ce.analysis.adaptation.adaptation import Adaptation
from ra2ce.analysis.adaptation.adaptation_option import AdaptationOption
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionAdaptation,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper
from tests import test_data, test_results
from tests.analysis.adaptation.conftest import AdaptationOptionCases


class TestAdaptation:
    @pytest.fixture(name="valid_adaptation_input")
    def _get_valid_adaptation_input_fixture(
        self,
        request: pytest.FixtureRequest,
        valid_analysis_ini: Path,
        valid_adaptation_config: AnalysisConfigData,
    ) -> Iterator[AnalysisInputWrapper]:
        _network_config_data = NetworkConfigData(
            static_path=test_results.joinpath(request.node.name, "static")
        )
        _network_config = NetworkConfigWrapper.from_data(
            valid_analysis_ini, _network_config_data
        )
        _config = AnalysisConfigWrapper.from_data_with_network(
            valid_analysis_ini, valid_adaptation_config, _network_config
        )

        _analysis_input = AnalysisInputWrapper.from_input(
            analysis=valid_adaptation_config.adaptation,
            analysis_config=_config,
            graph_file=_config.graph_files.base_graph_hazard,
            graph_file_hazard=_config.graph_files.base_graph_hazard,
        )

        yield _analysis_input

    @pytest.fixture(name="acceptance_adaptation_option")
    def test_initialize(self, valid_adaptation_input: AnalysisInputWrapper):
        # 1./2. Define test data./Run test.
        _adaptation = Adaptation(valid_adaptation_input)

        # 3. Verify expectations.
        assert isinstance(_adaptation, Adaptation)

    def test_execute_cost(
        self,
        request: pytest.FixtureRequest,
        valid_analysis_ini: Path,
        valid_adaptation_config: AnalysisConfigData,
    ):
        # 1. Define test data.
        _adaptation = Adaptation()
        _adaptation.analysis_input = None

        # 2. Run test.
        _result = _adaptation.run_cost()

        # 3. Verify expectations.
        assert isinstance(_result, GeoDataFrame)
        assert _result == 0.0

    @pytest.mark.parametrize(
        "adaptation_option",
        AdaptationOptionCases.cases,
    )
    def test_calculate_option_cost(
        self,
        valid_adaptation_input: AnalysisInputWrapper,
        valid_adaptation_config: AnalysisConfigData,
        adaptation_option: tuple[AnalysisSectionAdaptation, float],
    ):
        # 1. Define test data.
        _adaptation = Adaptation(valid_adaptation_input, valid_adaptation_config)
        _option = AdaptationOption.from_config(
            adaptation_option[0],
            valid_adaptation_config.damages_list[0],
            valid_adaptation_config.losses_list[0],
        )

        # 2. Run test.
        _cost = _adaptation.calculate_option_cost(_option)

        # 3. Verify expectations.
        assert _cost == pytest.approx(adaptation_option[1])
