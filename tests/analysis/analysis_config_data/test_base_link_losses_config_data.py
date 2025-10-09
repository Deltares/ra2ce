import math
from dataclasses import is_dataclass
from pathlib import Path

import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data_protocol import (
    AnalysisConfigDataProtocol,
)
from ra2ce.analysis.analysis_config_data.base_link_losses_config_data import (
    BaseLinkLossesConfigData,
    MultiLinkLossesConfigData,
    SingleLinkLossesConfigData,
)
from ra2ce.analysis.analysis_config_data.enums import weighing_enum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)
from ra2ce.analysis.analysis_config_data.enums.traffic_period_enum import (
    TrafficPeriodEnum,
)
from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.common.validation.validation_report import ValidationReport


@pytest.mark.parametrize(
    "link_losses_class", [SingleLinkLossesConfigData, MultiLinkLossesConfigData]
)
class TestLinkLossesConfigData:
    def test_initialize(self, link_losses_class: type[BaseLinkLossesConfigData]):
        # 1. Define test data.
        _data_name = "Test Link Losses Analysis"

        # 2. Run test.
        link_losses_config = link_losses_class(name=_data_name)

        # 3. Verify expectations.
        assert isinstance(link_losses_config, link_losses_class)
        assert isinstance(link_losses_config, BaseLinkLossesConfigData)
        assert isinstance(link_losses_config, AnalysisConfigDataProtocol)
        assert is_dataclass(link_losses_config)
        assert link_losses_config.name == _data_name
        assert link_losses_config.save_gpkg is False
        assert link_losses_config.save_csv is False
        assert link_losses_config.event_type == EventTypeEnum.NONE
        assert link_losses_config.weighing == WeighingEnum.NONE
        assert math.isnan(link_losses_config.production_loss_per_capita_per_hour)
        assert (
            link_losses_config.traffic_period == None
            or link_losses_config.traffic_period == TrafficPeriodEnum.DAY
        )
        assert (
            link_losses_config.trip_purposes == None
            or link_losses_config.trip_purposes == [TripPurposeEnum.NONE]
        )
        assert link_losses_config.resilience_curves_file is None
        assert link_losses_config.traffic_intensities_file is None
        assert link_losses_config.values_of_time_file is None
        assert link_losses_config.risk_calculation_mode == RiskCalculationModeEnum.NONE
        assert link_losses_config.risk_calculation_year is None

    @pytest.fixture(name="valid_link_losses_config")
    def fixture_valid_link_losses_config(self, link_losses_class: type[BaseLinkLossesConfigData]):
        return link_losses_class(
            name="Valid Link Losses Analysis",
            weighing=WeighingEnum.LENGTH,
            event_type=EventTypeEnum.EVENT,
            production_loss_per_capita_per_hour=10.0,
            traffic_period=TrafficPeriodEnum.DAY,
            trip_purposes=[TripPurposeEnum.BUSINESS],
            resilience_curves_file=Path(__file__),
            traffic_intensities_file=Path(__file__),
            values_of_time_file=Path(__file__),
            risk_calculation_mode=RiskCalculationModeEnum.NONE,
        )

    @pytest.mark.parametrize(
        "risk_calculation_year",
        [
            pytest.param(None, id="none year"),
            pytest.param(-5, id="negative year"),
            pytest.param(0, id="zero year"),
        ],
    )
    def test_given_risk_calculation_triangle_and_invalid_year_when_validate_integrity_then_fails(
        self,
        risk_calculation_year: int | None,
        valid_link_losses_config: type[BaseLinkLossesConfigData],
    ):
        # 1. Define test data.
        _data_name = "Invalid Damages Analysis"
        # Set risk calculation mode to TRIANGLE_TO_NULL_YEAR to trigger the year validation.
        _damages_config = valid_link_losses_config
        _damages_config.name = _data_name
        _damages_config.risk_calculation_mode = RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR
        _damages_config.risk_calculation_year = risk_calculation_year

        _expected_error = f"For link losses analysis '{_data_name}': 'risk_calculation_year' should be a positive integer when 'risk_calculation_mode' is set to 'RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR'."

        # 2. Run test.
        _report = _damages_config.validate_integrity()

        # 3. Verify expectations for invalid data.
        assert isinstance(_report, ValidationReport)
        assert (
            not _report.is_valid()
        ), "Expected invalid report due to negative risk_calculation_year"
        assert len(_report._errors) == 1
        assert _report._errors[0] == _expected_error

    def test_given_risk_calculation_triangle_and_valid_year_when_validate_integrity_then_succeeds(
        self, valid_link_losses_config: type[BaseLinkLossesConfigData],
    ):
        # 1. Define test data.
        _data_name = "Invalid Damages Analysis"
        _damages_config = valid_link_losses_config
        _damages_config.name = _data_name
        _damages_config.risk_calculation_mode = RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR
        _damages_config.risk_calculation_year = 10

        # 2. Run test.
        _report = _damages_config.validate_integrity()

        # 3. Verify expectations for invalid data.
        assert isinstance(_report, ValidationReport)
        assert (
            _report.is_valid()
        ), "Expected valid report due to possitive risk_calculation_year"

    @pytest.mark.parametrize(
        "risk_calculation_mode",
        [
            pytest.param(_mode, id=_mode.name)
            for _mode in RiskCalculationModeEnum
            if _mode != RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR
        ],
    )
    @pytest.mark.parametrize("risk_calculation_year", [(None), (-5), (0), (2)])
    def test_given_any_non_triangle_risk_calculation_when_validate_integrity_then_succeeds(
        self,
        risk_calculation_mode: RiskCalculationModeEnum,
        risk_calculation_year: int | None,
        link_losses_class: type[BaseLinkLossesConfigData],
    ):
        # 1. Define test data.
        _data_name = "Valid Damages Analysis"
        _damages_config = link_losses_class(
            name=_data_name,
            risk_calculation_mode=risk_calculation_mode,
            risk_calculation_year=risk_calculation_year,
            weighing=WeighingEnum.LENGTH,
            event_type=EventTypeEnum.EVENT,
            production_loss_per_capita_per_hour=10.0,
            traffic_period=TrafficPeriodEnum.DAY,
            trip_purposes=[TripPurposeEnum.BUSINESS],
            resilience_curves_file=Path(__file__),
            traffic_intensities_file=Path(__file__),
            values_of_time_file=Path(__file__),

        )

        # 2. Run test.
        _report = _damages_config.validate_integrity()

        # 3. Verify expectations for invalid data.
        assert isinstance(_report, ValidationReport)
        assert (
            _report.is_valid()
        ), "Expected valid report due to non-triangle risk calculation mode"
