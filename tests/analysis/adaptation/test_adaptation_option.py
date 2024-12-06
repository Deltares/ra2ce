from dataclasses import dataclass

import pytest

from ra2ce.analysis.adaptation.adaptation_option import AdaptationOption
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionAdaptation,
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
        valid_adaptation_config: tuple[AnalysisInputWrapper, AnalysisConfigWrapper],
        losses_analysis_type: AnalysisLossesEnum,
        losses_analysis: type[SingleLinkLosses | MultiLinkLosses],
    ):
        # 1. Define test data.
        _config_data = valid_adaptation_config[1].config_data
        assert _config_data.adaptation
        _config_data.adaptation.losses_analysis = losses_analysis_type
        _config_option = _config_data.adaptation.adaptation_options[0]

        # 2. Run test.
        _option = AdaptationOption.from_config(
            analysis_config=valid_adaptation_config[1],
            adaptation_option=_config_option,
        )

        # 3. Verify expectations.
        assert isinstance(_option, AdaptationOption)
        assert _option.id == _config_option.id
        assert len(_option.analyses) == 2
        assert Damages in [x.analysis_class for x in _option.analyses]
        assert losses_analysis in [x.analysis_class for x in _option.analyses]

    def test_from_config_no_damages_losses_raises(self):
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
            "Damages and losses sections are required to create an adaptation option."
        )

    @pytest.mark.parametrize(
        "constr_cost, constr_interval, maint_cost, maint_interval, net_unit_cost",
        [
            pytest.param(0.0, 0.0, 0.0, 0.0, 0.0, id="Zero costs and intervals"),
            pytest.param(
                1000.0, 10.0, 200.0, 3.0, 2714.560799, id="Cheap constr, exp maint"
            ),
            pytest.param(
                5000.0, 100.0, 50.0, 3.0, 5233.340599, id="Exp constr, cheap maint"
            ),
            pytest.param(
                0.0, 0.0, 1100.0, 1.0, 17148.078514, id="Zero constr cost and interval"
            ),
            pytest.param(
                1000.0, 100.0, 0.0, 0.0, 1000.0, id="Zero maint const and interval"
            ),
            pytest.param(
                1000.0, 8.0, 100.0, 2.0, 3264.2066789, id="Coinciding intervals"
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
