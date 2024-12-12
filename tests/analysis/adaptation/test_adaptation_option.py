from dataclasses import dataclass

import pytest
from geopandas import GeoDataFrame
from pandas import Series

from ra2ce.analysis.adaptation.adaptation_option import AdaptationOption
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionAdaptation,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
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
                adaptation_option=AnalysisSectionAdaptation(),
            )

        # 3. Verify expectations.
        assert _exc.match(
            "Damages and/or losses sections are required to create an adaptation option."
        )

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
    def test_calculate_unit_cost_returns_float(
        self,
        constr_cost: float,
        constr_interval: float,
        maint_cost: float,
        maint_interval: float,
        net_unit_cost: float,
    ):
        # Mock to avoid complex setup.
        @dataclass
        class MockAdaptationOption(AdaptationOption):
            id: str

        # 1. Define test data.
        _option = MockAdaptationOption(
            id="AnOption",
            name=None,
            construction_cost=constr_cost,
            construction_interval=constr_interval,
            maintenance_cost=maint_cost,
            maintenance_interval=maint_interval,
            analyses=[],
            analysis_config=None,
        )
        _time_horizon = 20.0
        _discount_rate = 0.025

        # 2. Run test.
        _result = _option.calculate_unit_cost(_time_horizon, _discount_rate)

        # 3. Verify expectations.
        assert isinstance(_result, float)
        assert _result == pytest.approx(net_unit_cost)

    def test_calculate_impact_returns_gdf(self) -> GeoDataFrame:
        @dataclass
        # Mock to avoid the need to run the impact analysis.
        class MockAdaptationOptionAnalysis:
            analysis_type: AnalysisDamagesEnum | AnalysisLossesEnum
            result_col: str
            result: float

            def execute(self, _: AnalysisConfigWrapper) -> Series:
                return Series(self.result, index=range(_nof_rows))

        # 1. Define test data.
        _nof_rows = 10
        _analyses = [
            MockAdaptationOptionAnalysis(
                analysis_type=_analysis_type,
                result_col=f"Result_{i}",
                result=(i + 1) * 1.0e6,
            )
            for i, _analysis_type in zip(
                range(2),
                [AnalysisDamagesEnum.DAMAGES, AnalysisLossesEnum.MULTI_LINK_LOSSES],
            )
        ]
        _id = "Option1"
        _option = AdaptationOption(
            id=_id,
            name=None,
            construction_cost=None,
            construction_interval=None,
            maintenance_cost=None,
            maintenance_interval=None,
            analyses=_analyses,
            analysis_config=None,
        )

        # 2. Run test.
        _result = _option.calculate_impact(1.0)

        # 3. Verify expectations.
        assert isinstance(_result, GeoDataFrame)
        assert _result[_option.impact_col].sum() == pytest.approx(
            _nof_rows * sum(x.result for x in _analyses)
        )
