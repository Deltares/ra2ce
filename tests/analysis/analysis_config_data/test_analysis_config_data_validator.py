import shutil
from typing import Any, Callable, Iterator

import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionBase,
    AnalysisSectionDamages,
    AnalysisSectionLosses,
    ProjectSection,
)
from ra2ce.analysis.analysis_config_data.analysis_config_data_validator import (
    AnalysisConfigDataValidator,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_enum import AnalysisEnum
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.common.validation.ra2ce_validator_protocol import Ra2ceIoValidator
from ra2ce.common.validation.validation_report import ValidationReport
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.network_config_data import NetworkSection
from tests import test_results


class TestAnalysisConfigDataValidator:
    def test_init_validator(self):
        # 1. Define test data.
        _test_config_data = AnalysisConfigData()

        # 2. Run test.
        _validator = AnalysisConfigDataValidator(_test_config_data)

        # 3. Verify expectations.
        assert isinstance(_validator, AnalysisConfigDataValidator)
        assert isinstance(_validator, Ra2ceIoValidator)

    def _validate_config(self, config_data: AnalysisConfigData) -> ValidationReport:
        _validator = AnalysisConfigDataValidator(config_data)
        return _validator.validate()

    def test_validate_with_required_headers(self, request: pytest.FixtureRequest):
        # 1. Define test data.
        _output_dir = test_results.joinpath(request.node.name)
        if _output_dir.exists():
            shutil.rmtree(_output_dir)
        _output_dir.mkdir(parents=True)

        # 2. Run test.
        _test_config_data = AnalysisConfigData(
            project=ProjectSection(),
            analyses=[
                AnalysisSectionDamages(
                    analysis=AnalysisDamagesEnum.DAMAGES,
                    event_type=EventTypeEnum.EVENT,
                    damage_curve=DamageCurveEnum.HZ,
                )
            ],
            output_path=_output_dir,
        )
        _report = self._validate_config(_test_config_data)

        # 3. Verify expectations.
        assert _report.is_valid()

    def _validate_headers(
        self, config_data: AnalysisConfigData, required_headers: list[str]
    ) -> ValidationReport:
        _validator = AnalysisConfigDataValidator(config_data)
        return _validator._validate_headers(required_headers)

    def test_validate_headers_fails_when_missing_expected_header(self):
        # 1. Define test data.
        _test_config_data = AnalysisConfigData()
        _missing_header = "Deltares"
        _expected_err = f"Property [ {_missing_header} ] is not configured. Add property [ {_missing_header} ] to the *.ini file. "

        # 2. Run test.
        _report = self._validate_headers(
            _test_config_data, required_headers=[_missing_header]
        )

        # 3. Verify final expectations.
        assert not _report.is_valid()
        assert _expected_err in _report._errors

    def test_validate_headers_fails_when_invalid_value(self):
        # 1. Define test data.
        _test_config_data = AnalysisConfigData(
            root_path=test_results,
            output_path=test_results.joinpath("output"),
            project=ProjectSection(),
            analyses=[AnalysisSectionDamages(analysis="invalid_analysis_type")],
        )

        # 2. Run test.
        _report = self._validate_headers(
            _test_config_data, required_headers=["analyses"]
        )

        # 3. Verify final expectations.
        assert not _report.is_valid()
        assert len(_report._errors) == 3

    @pytest.fixture(name="section_losses_analysis_config")
    def _get_section_losses_analysis_config_generator(
        self,
    ) -> Iterator[Callable[str, AnalysisConfigData]]:
        yield lambda file_id: AnalysisConfigData(
            root_path=test_results,
            output_path=test_results.joinpath("output"),
            network=NetworkSection(source=SourceEnum.SHAPEFILE, file_id=file_id),
            project=ProjectSection(),
            analyses=[
                AnalysisSectionLosses(
                    name="Test Analysis",
                    analysis=AnalysisLossesEnum.MULTI_LINK_LOSSES,
                )
            ],
        )

    def test_validate_given_shp_network_without_id_when_multi_link_losses_then_fails(
        self, section_losses_analysis_config: Callable[str, AnalysisConfigData]
    ):
        # 1. Define test data.
        _test_config_data = section_losses_analysis_config(None)
        assert _test_config_data.network.source == SourceEnum.SHAPEFILE
        assert _test_config_data.network.file_id is None

        # 2. Run test
        _report = self._validate_config(_test_config_data)

        # 3. Verify final expectations
        assert not _report.is_valid()
        assert len(_report._errors) == 1
        assert (
            _report._errors[0]
            == "Not possible to create analysis 'Test Analysis' - Shapefile used as source, but no 'file_id' configured for the 'NetworkSection'."
        )

    def test_validate_given_shp_network_with_id_when_multi_link_losses_then_succeeds(
        self, section_losses_analysis_config: Callable[str, AnalysisConfigData]
    ):
        # 1. Define test data.
        _test_config_data = section_losses_analysis_config("dummy")
        assert _test_config_data.network.source == SourceEnum.SHAPEFILE
        assert _test_config_data.network.file_id is not None

        # 2. Run test
        _report = self._validate_config(_test_config_data)

        # 3. Verify final expectations
        assert _report.is_valid()

    @pytest.mark.parametrize(
        "analysis_enum",
        [
            pytest.param(_option, id=str(_option.name))
            for _option in [
                ale
                for ale in AnalysisLossesEnum.list_valid_options()
                if ale != AnalysisLossesEnum.MULTI_LINK_LOSSES
            ]
            + [ade for ade in AnalysisDamagesEnum.list_valid_options()]
            + [ae for ae in AnalysisEnum.list_valid_options()]
        ],
    )
    def test_validate_given_shp_network_without_id_when_any_valid_analysis_given_then_succeeds(
        self, analysis_enum: Any
    ):
        # 1. Define test data
        _test_config_data = AnalysisConfigData(
            root_path=test_results,
            output_path=test_results.joinpath("output"),
            network=NetworkSection(source=SourceEnum.SHAPEFILE, file_id=None),
            project=ProjectSection(),
            analyses=[
                AnalysisSectionBase(name="Test Analysis", analysis=analysis_enum)
            ],
        )

        # 2. Run test
        _report = self._validate_config(_test_config_data)

        # 3. Verify final expectations.
        assert _report.is_valid()

    @pytest.mark.parametrize(
        "analysis_enum",
        [
            pytest.param(AnalysisLossesEnum.INVALID, id="Losses - Invalid"),
            pytest.param(AnalysisDamagesEnum.INVALID, id="Damages - Invalid"),
            pytest.param(AnalysisEnum.INVALID, id="General - Invalid"),
        ],
    )
    def test_validate_given_shp_network_without_id_when_invalid_analysis_given_then_fails(
        self, analysis_enum: Any
    ):
        # 1. Define test data
        _test_config_data = AnalysisConfigData(
            root_path=test_results,
            output_path=test_results.joinpath("output"),
            network=NetworkSection(source=SourceEnum.SHAPEFILE, file_id=None),
            project=ProjectSection(),
            analyses=[
                AnalysisSectionBase(name="Test Analysis", analysis=analysis_enum)
            ],
        )

        # 2. Run test
        _report = self._validate_config(_test_config_data)

        # 3. Verify final expectations.
        assert not _report.is_valid()
        # The errors are not actually related to our network compatibility issue.
        assert not any(
            _re
            for _re in _report._errors
            if _re.startswith("Not possible to create analysis 'Test Analysis'")
        )
