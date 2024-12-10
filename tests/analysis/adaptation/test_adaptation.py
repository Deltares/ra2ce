from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pytest
from geopandas import GeoDataFrame
from shapely import Point

from ra2ce.analysis.adaptation.adaptation import Adaptation
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
        valid_adaptation_config: tuple[AnalysisInputWrapper, AnalysisConfigWrapper],
    ):
        # 1./2. Define test data./Run test.
        _adaptation = Adaptation(valid_adaptation_config[0], valid_adaptation_config[1])

        # 3. Verify expectations.
        assert isinstance(_adaptation, Adaptation)
        assert isinstance(_adaptation, AnalysisBase)

    def test_run_cost_returns_gdf(
        self,
        valid_adaptation_config: tuple[AnalysisInputWrapper, AnalysisConfigWrapper],
    ):
        # 1. Define test data.
        _adaptation = Adaptation(valid_adaptation_config[0], valid_adaptation_config[1])

        # 2. Run test.
        _result = _adaptation.run_cost()

        # 3. Verify expectations.
        assert isinstance(_result, GeoDataFrame)
        assert all(
            f"{_option.id}_cost" in _result.columns
            for _option in _adaptation.adaptation_collection.adaptation_options
        )
        for _option, _expected in AdaptationOptionCases.cases[1:]:
            assert _result[f"{_option.id}_cost"].sum(axis=0) == pytest.approx(
                _expected[0]
            )

    def test_run_benefit_returns_gdf(
        self,
        valid_adaptation_config: tuple[AnalysisInputWrapper, AnalysisConfigWrapper],
    ):
        # 1. Define test data.
        _adaptation = Adaptation(valid_adaptation_config[0], valid_adaptation_config[1])

        # 2. Run test.
        _result = _adaptation.run_benefit()

        # 3. Verify expectations.
        assert isinstance(_result, GeoDataFrame)
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

    @pytest.fixture
    def valid_gdf(self) -> GeoDataFrame:
        return GeoDataFrame(
            geometry=[Point(x, 0) for x in range(10)],
            crs="EPSG:4326",
        )
        # return GeoDataFrame.from_dict(
        #     {"u": range(10), "v": range(10)},
        #     geometry=[Point(x, 0) for x in range(10)],
        #     crs="EPSG:4326",
        # )

    @pytest.fixture(name="mocked_adaptation")
    def _get_mocked_adaptation_fixture(
        self, valid_gdf: GeoDataFrame
    ) -> Iterator[Adaptation]:
        # Mock to avoid complex setup.
        @dataclass
        class MockAdaptationOption:
            id: str

        class MockAdaptation(Adaptation):
            graph_file_hazard = NetworkFile(
                graph=valid_gdf,
            )
            adaptation_collection: AdaptationOptionCollection = (
                AdaptationOptionCollection(
                    all_options=[
                        MockAdaptationOption(id=f"Option{x}") for x in range(2)
                    ]
                )
            )

            def __init__(self):
                pass

        yield MockAdaptation()

    def test_calculate_bc_ratio_returns_gdf(
        self, mocked_adaptation: Adaptation, valid_gdf: GeoDataFrame
    ):
        # 1. Define test data.
        _benefit_gdf = valid_gdf
        _cost_gdf = valid_gdf

        for i, _option in enumerate(
            mocked_adaptation.adaptation_collection.adaptation_options
        ):
            _benefit_gdf[f"{_option.id}_benefit"] = 4.0 + i
            _cost_gdf[f"{_option.id}_cost"] = 1.0 + i

        # 2. Run test.
        _result = mocked_adaptation.calculate_bc_ratio(_benefit_gdf, _cost_gdf)

        # 3. Verify expectations.
        assert isinstance(_result, GeoDataFrame)
        assert "geometry" in _result.columns
        assert all(
            [
                f"{_option.id}_bc_ratio" in _result.columns
                for _option in mocked_adaptation.adaptation_collection.adaptation_options
            ]
        )
        for i, _option in enumerate(
            mocked_adaptation.adaptation_collection.adaptation_options
        ):
            assert _result[f"{_option.id}_bc_ratio"].sum(axis=0) == pytest.approx(
                10 * (4.0 + i) / (1.0 + i)
            )

    def test_output_gdf_can_be_exported_to_gpkg(
        self,
        valid_adaptation_config: tuple[AnalysisInputWrapper, AnalysisConfigWrapper],
        test_result_param_case: Path,
    ):
        # 1. Define test data.
        _adaptation = Adaptation(valid_adaptation_config[0], valid_adaptation_config[1])

        # 2. Run test.
        _result = _adaptation.execute().results_collection[0]

        _output_path = _result.output_path
        _output_path.mkdir(parents=True, exist_ok=True)

        _result.analysis_result.to_file(
            _result.output_path.joinpath("adaptation_output.gpkg"), driver="GPKG"
        )

        # 3. Verify expectations.
        assert test_result_param_case.exists()
