from pathlib import Path
from typing import Iterator

import pytest
from geopandas import GeoDataFrame

from ra2ce.analysis.adaptation.adaptation import Adaptation
from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper
from tests import test_results


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
            graph_file=_config.graph_files.base_network,
            graph_file_hazard=_config.graph_files.base_network_hazard,
        )

        yield _analysis_input

    def test_initialize(
        self,
        valid_adaptation_input: AnalysisInputWrapper,
        valid_adaptation_config: AnalysisConfigData,
    ):
        # 1./2. Define test data./Run test.
        _adaptation = Adaptation(valid_adaptation_input, valid_adaptation_config)

        # 3. Verify expectations.
        assert isinstance(_adaptation, Adaptation)
        assert isinstance(_adaptation, AnalysisBase)

    def test_run_cost(
        self,
        valid_adaptation_input: AnalysisInputWrapper,
        valid_adaptation_config: AnalysisConfigData,
    ):
        # 1. Define test data.
        _adaptation = Adaptation(valid_adaptation_input, valid_adaptation_config)

        # 2. Run test.
        _cost_gdf = _adaptation.run_cost()

        # 3. Verify expectations.
        assert isinstance(_cost_gdf, GeoDataFrame)
        assert all(
            [
                f"costs_{_option.id}" in _cost_gdf.columns
                for _option in _adaptation.adaptation_collection.adaptation_options
            ]
        )
