from typing import Iterator

import pytest
from geopandas import GeoDataFrame
from pandas import DataFrame
from shapely import Point

from ra2ce.analysis.adaptation.adaptation import Adaptation
from ra2ce.analysis.adaptation.adaptation_option import AdaptationOption
from ra2ce.analysis.adaptation.adaptation_option_collection import (
    AdaptationOptionCollection,
)
from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.network.graph_files.network_file import NetworkFile
from tests.analysis.adaptation.conftest import AdaptationOptionCases


class TestAdaptation:
    def test_initialize(
        self,
        valid_adaptation_config_with_input: tuple[
            AnalysisInputWrapper, AnalysisConfigWrapper
        ],
    ):
        # 1./2. Define test data./Run test.
        _adaptation = Adaptation(
            valid_adaptation_config_with_input[0], valid_adaptation_config_with_input[1]
        )

        # 3. Verify expectations.
        assert isinstance(_adaptation, Adaptation)
        assert isinstance(_adaptation, AnalysisBase)

    def test_run_cost_returns_df(
        self,
        valid_adaptation_config_with_input: tuple[
            AnalysisInputWrapper, AnalysisConfigWrapper
        ],
    ):
        # 1. Define test data.
        _adaptation = Adaptation(
            valid_adaptation_config_with_input[0], valid_adaptation_config_with_input[1]
        )

        # 2. Run test.
        _result = _adaptation.run_cost()

        # 3. Verify expectations.
        assert isinstance(_result, DataFrame)
        assert all(
            _option.cost_col in _result.columns
            for _option in _adaptation.adaptation_collection.adaptation_options
        )
        for _option, _expected in AdaptationOptionCases.cases[1:]:
            assert _result[f"{_option.id}_cost"].sum(axis=0) == pytest.approx(
                _expected[0]
            )

    def test_run_benefit_returns_df(
        self,
        valid_adaptation_config_with_input: tuple[
            AnalysisInputWrapper, AnalysisConfigWrapper
        ],
    ):
        # 1. Define test data.
        _adaptation = Adaptation(
            valid_adaptation_config_with_input[0], valid_adaptation_config_with_input[1]
        )

        # 2. Run test.
        _result = _adaptation.run_benefit()

        # 3. Verify expectations.
        assert isinstance(_result, DataFrame)
        assert all(
            [
                f"{_option.id}_benefit" in _result.columns
                for _option in _adaptation.adaptation_collection.adaptation_options
            ]
        )
        for _option, _expected in AdaptationOptionCases.cases[1:]:
            assert _result[f"{_option.id}_benefit"].sum(axis=0) == pytest.approx(
                _expected[1]
            )

    @pytest.fixture(name="mocked_adaptation")
    def _get_mocked_adaptation_fixture(self) -> Iterator[Adaptation]:
        # Mock to avoid complex setup.
        class MockAdaptation(Adaptation):
            graph_file_hazard = NetworkFile(
                graph=GeoDataFrame.from_dict(
                    data={
                        "link_id": range(10),
                        "geometry": [Point(x, 0) for x in range(10)],
                        "highway": "residential",
                        "length": 1.0,
                    },
                    geometry="geometry",
                )
            )
            adaptation_collection: AdaptationOptionCollection = (
                AdaptationOptionCollection(
                    all_options=[
                        AdaptationOption(
                            id=f"Option{x}",
                            name=None,
                            construction_cost=None,
                            construction_interval=None,
                            maintenance_cost=None,
                            maintenance_interval=None,
                            analyses=None,
                            analysis_config=None,
                        )
                        for x in range(2)
                    ]
                )
            )

            def __init__(self):
                pass

        yield MockAdaptation()

    def test_calculate_bc_ratio_returns_gdf(self, mocked_adaptation: Adaptation):
        # 1. Define test data.
        _id_col = "link_id"
        _nof_rows = 10
        _benefit_df = DataFrame.from_dict({_id_col: range(_nof_rows)})
        _cost_df = DataFrame.from_dict({_id_col: range(_nof_rows)})

        for i, _option in enumerate(
            mocked_adaptation.adaptation_collection.adaptation_options
        ):
            _benefit_df[_option.benefit_col] = 4.0 + i
            _cost_df[_option.cost_col] = 1.0 + i

        # 2. Run test.
        _result = mocked_adaptation.calculate_bc_ratio(_benefit_df, _cost_df)

        # 3. Verify expectations.
        assert isinstance(_result, GeoDataFrame)
        assert not _result.geometry.empty
        assert all(
            [
                _option.bc_ratio_col in _result.columns
                for _option in mocked_adaptation.adaptation_collection.adaptation_options
            ]
        )
        for i, _option in enumerate(
            mocked_adaptation.adaptation_collection.adaptation_options
        ):
            assert _result[_option.bc_ratio_col].sum(axis=0) == pytest.approx(
                _nof_rows * (4.0 + i) / (1.0 + i)
            )

    def test_calculate_bc_ratio_matches_on_link_id(self, mocked_adaptation: Adaptation):
        # 1. Define test data.
        _id_col = "link_id"
        _custom_id = [5, 6, 7, 8, 9, 0, 1, 2, 3, 4]
        _benefit_df = DataFrame.from_dict(
            {
                _id_col: _custom_id,
                "Option1_benefit": [i + 1 for i in _custom_id],
            }
        )
        _cost_df = DataFrame.from_dict(
            {
                _id_col: list(reversed(_custom_id)),
                "Option1_cost": [i + 1 for i in reversed(_custom_id)],
            }
        )

        # 2. Run test.
        _benefit_df = mocked_adaptation.calculate_bc_ratio(_benefit_df, _cost_df)

        # 3. Verify expectations.
        assert _benefit_df[
            mocked_adaptation.adaptation_collection.adaptation_options[0].bc_ratio_col
        ].sum(axis=0) == pytest.approx(10.0)
