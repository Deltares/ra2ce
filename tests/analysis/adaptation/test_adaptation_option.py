from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import pytest
from geopandas import GeoDataFrame
from pandas import DataFrame
from shapely import Point

from ra2ce.analysis.adaptation.adaptation_option import AdaptationOption
from ra2ce.analysis.adaptation.adaptation_option_analysis import (
    AdaptationOptionAnalysis,
)
from ra2ce.analysis.adaptation.adaptation_option_partial_result import (
    AdaptationOptionPartialResult,
)
from ra2ce.analysis.adaptation.adaptation_result_enum import AdaptationResultEnum
from ra2ce.analysis.adaptation.adaptation_settings import AdaptationSettings
from ra2ce.analysis.analysis_config_data.adaptation_config_data import (
    AdaptationConfigData,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.damages.damages import Damages
from ra2ce.analysis.losses.multi_link_losses import MultiLinkLosses
from ra2ce.analysis.losses.single_link_losses import SingleLinkLosses


class TestAdaptationOption:
    @pytest.mark.parametrize(
        "losses_analysis_type, losses_analysis",
        [
            (AnalysisLossesEnum.SINGLE_LINK_LOSSES, SingleLinkLosses),
            (AnalysisLossesEnum.MULTI_LINK_LOSSES, MultiLinkLosses),
        ],
    )
    def test_from_config_returns_object_with_2_analyses(
        self,
        valid_adaptation_config: AnalysisConfigWrapper,
        losses_analysis_type: AnalysisLossesEnum,
        losses_analysis: type[SingleLinkLosses | MultiLinkLosses],
    ):
        # 1. Define test data.
        _config_data = valid_adaptation_config.config_data
        assert _config_data.adaptation
        _config_data.adaptation.losses_analysis = losses_analysis_type

        _config_option = _config_data.adaptation.adaptation_options[0]

        # 2. Run test.
        _result = AdaptationOption.from_config(
            analysis_config=valid_adaptation_config,
            adaptation_option=_config_option,
        )

        # 3. Verify expectations.
        assert isinstance(_result, AdaptationOption)
        assert _result.id == _config_option.id
        assert len(_result.analyses) == 2
        assert Damages in [x.analysis_class for x in _result.analyses]
        assert losses_analysis in [x.analysis_class for x in _result.analyses]

    @pytest.mark.parametrize(
        "keep_analyses",
        [
            pytest.param("damages_list", id="Only damages"),
            pytest.param("losses_list", id="Only losses"),
        ],
    )
    def test_from_config_only_damages_or_losses_returns_object_with_1_analysis(
        self,
        valid_adaptation_config: AnalysisConfigWrapper,
        keep_analyses: str,
    ):
        # 1. Define test data.
        _config_data = valid_adaptation_config.config_data
        assert _config_data.adaptation
        # Keep the given analyses and the adaptation.
        _keep_list = getattr(_config_data, keep_analyses)
        _config_data.analyses = _keep_list + [_config_data.adaptation]

        _config_option = _config_data.adaptation.adaptation_options[0]

        # 2. Run test.
        _result = AdaptationOption.from_config(
            analysis_config=valid_adaptation_config,
            adaptation_option=_config_option,
        )

        # 3. Verify expectations.
        assert isinstance(_result, AdaptationOption)
        assert _result.id == _config_option.id
        assert len(_result.analyses) == 1

    def test_from_config_no_damages_and_no_losses_raises(self):
        # 1. Define test data.
        _config = AnalysisConfigWrapper()

        # 2. Run test.
        with pytest.raises(ValueError) as _exc:
            AdaptationOption.from_config(
                analysis_config=_config,
                adaptation_option=AdaptationConfigData(),
            )

        # 3. Verify expectations.
        assert _exc.match(
            "Damages and/or losses sections are required to create an adaptation option."
        )

    @dataclass
    # Mock to avoid the need to run the impact analyses.
    class MockAdaptationOptionAnalysis(AdaptationOptionAnalysis):
        result: float

        def execute(self, _: AnalysisConfigWrapper) -> DataFrame:
            return AdaptationOptionPartialResult(
                option_id=self.option_id,
                data_frame=GeoDataFrame.from_dict(
                    {
                        "rfid": range(10),
                        f"{self.option_id}_{self.analysis_type.config_value}": self.result,
                    }
                ),
            )

    @pytest.fixture(name="valid_adaptation_option")
    def _get_valid_adaptation_option_fixture(self) -> Iterator[AdaptationOption]:
        _option_id = "Option1"
        yield AdaptationOption(
            id=_option_id,
            name=None,
            construction_cost=1000.0,
            construction_interval=10.0,
            maintenance_cost=200.0,
            maintenance_interval=3.0,
            analyses=[
                TestAdaptationOption.MockAdaptationOptionAnalysis(
                    option_id=_option_id,
                    analysis_type=AnalysisDamagesEnum.DAMAGES,
                    analysis_class=None,
                    analysis_input=None,
                    result_col=f"Result_{_option_id}",
                    result=1.0,
                )
            ],
            analysis_config=None,
            adaptation_settings=AdaptationSettings(
                discount_rate=0.025,
                time_horizon=20.0,
                initial_frequency=0.01,
                climate_factor=0.001,
            ),
        )

    @pytest.fixture(name="valid_reference_impact")
    def _get_valid_reference_impact_fixture(
        self,
    ) -> Iterator[AdaptationOptionPartialResult]:
        _ref_option_id = "Option0"
        _result = AdaptationOptionPartialResult(
            option_id=_ref_option_id,
            data_frame=GeoDataFrame.from_dict(
                {
                    "rfid": range(10),
                    f"{_ref_option_id}_net_impact": range(10),
                    "geometry": Point(0, 0),
                }
            ),
        )
        _result.option_id = _ref_option_id

        yield _result

    def test_get_bc_ratio_returns_result(
        self,
        valid_adaptation_option: AdaptationOption,
        valid_reference_impact: AdaptationOptionPartialResult,
    ):
        # 1. Define test data.
        _gdf_in = GeoDataFrame.from_dict(
            {
                "rfid": range(10),
                "geometry": Point(0, 0),
                "length": 2.4,
                "EV1_fr": 0.4,
            }
        )
        _hazard_fraction_cost = True

        # 2. Run test.
        _result = valid_adaptation_option.get_bc_ratio(
            valid_reference_impact, _gdf_in, _hazard_fraction_cost
        )

        # 3. Verify expectations.
        assert isinstance(_result, AdaptationOptionPartialResult)
        assert _result.data_frame[
            f"{valid_adaptation_option.id}_bc_ratio"
        ].sum() == pytest.approx(0.0161828)

    def test__get_benefit_returns_result(
        self,
        valid_adaptation_option: AdaptationOption,
        valid_reference_impact: AdaptationOptionPartialResult,
    ):
        # 1. Run test.
        _result = valid_adaptation_option._get_benefit(valid_reference_impact)

        # 2. Verify expectations.
        assert isinstance(_result, AdaptationOptionPartialResult)
        assert _result.data_frame[
            f"{valid_adaptation_option.id}_benefit"
        ].sum() == pytest.approx(42.014776)

    @pytest.mark.parametrize(
        "hazard_fraction_cost, expected",
        [
            pytest.param(True, 25962.604172, id="With fraction cost"),
            pytest.param(False, 64906.510430, id="Without fraction cost"),
        ],
    )
    def test__get_cost_returns_result(
        self,
        valid_adaptation_option: AdaptationOption,
        hazard_fraction_cost: bool,
        expected: float,
    ):
        # 1. Define test data.
        _gdf_in = GeoDataFrame.from_dict(
            {
                "rfid": range(10),
                "geometry": Point(0, 0),
                "length": 2.4,
                "EV1_fr": 0.4,
            }
        )

        # 2. Run test.
        _result = valid_adaptation_option._get_cost(_gdf_in, hazard_fraction_cost)

        # 3. Verify expectations.
        assert isinstance(_result, AdaptationOptionPartialResult)
        assert _result.data_frame[
            f"{valid_adaptation_option.id}_cost"
        ].sum() == pytest.approx(expected)

    @pytest.mark.parametrize(
        "constr_cost, constr_interval, maint_cost, maint_interval, net_unit_cost",
        [
            pytest.param(0.0, 0.0, 0.0, 0.0, 0.0, id="Zero costs and intervals"),
            pytest.param(
                1000.0, 10.0, 200.0, 3.0, 2704.437935, id="Cheap constr, exp maint"
            ),
            pytest.param(
                5000.0, 100.0, 50.0, 3.0, 5233.340599, id="Exp constr, cheap maint"
            ),
            pytest.param(
                0.0, 0.0, 1100.0, 1.0, 17576.780477, id="Zero constr cost and interval"
            ),
            pytest.param(
                1000.0, 100.0, 0.0, 0.0, 1000.0, id="Zero maint cost and interval"
            ),
            pytest.param(
                1000.0, 8.0, 100.0, 2.0, 3053.742434, id="Coinciding intervals"
            ),
        ],
    )
    def test__get_unit_cost_returns_float(
        self,
        valid_adaptation_option: AdaptationOption,
        constr_cost: float,
        constr_interval: float,
        maint_cost: float,
        maint_interval: float,
        net_unit_cost: float,
    ):
        # 1. Define test data.
        valid_adaptation_option.construction_cost = constr_cost
        valid_adaptation_option.construction_interval = constr_interval
        valid_adaptation_option.maintenance_cost = maint_cost
        valid_adaptation_option.maintenance_interval = maint_interval

        # 2. Run test.
        _result = valid_adaptation_option._get_unit_cost()

        # 3. Verify expectations.
        assert isinstance(_result, float)
        assert _result == pytest.approx(net_unit_cost)

    def test_get_impact_returns_result(self, valid_adaptation_option: AdaptationOption):
        # 1. Define test data.
        _nof_rows = 10
        valid_adaptation_option.analyses = [
            TestAdaptationOption.MockAdaptationOptionAnalysis(
                option_id=valid_adaptation_option.id,
                analysis_type=_analysis_type,
                analysis_class=None,
                analysis_input=None,
                result_col=f"Result_{i}",
                result=(i + 1) * 1.0e6,
            )
            for i, _analysis_type in zip(
                range(2),
                [AnalysisDamagesEnum.DAMAGES, AnalysisLossesEnum.MULTI_LINK_LOSSES],
            )
        ]

        # 2. Run test.
        _result = valid_adaptation_option.get_impact()

        # 3. Verify expectations.
        assert isinstance(_result, AdaptationOptionPartialResult)
        assert _result.data_frame[
            f"{valid_adaptation_option.id}_{AdaptationResultEnum.EVENT_IMPACT}"
        ].sum() == pytest.approx(
            _nof_rows * sum(x.result for x in valid_adaptation_option.analyses)
        )
