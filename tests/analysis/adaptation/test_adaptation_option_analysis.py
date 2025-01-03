from pathlib import Path

import pytest
from geopandas import GeoDataFrame
from pandas import Series

from ra2ce.analysis.adaptation.adaptation_option_analysis import (
    AdaptationOptionAnalysis,
)
from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_protocol import AnalysisProtocol
from ra2ce.analysis.damages.damages import Damages
from ra2ce.analysis.losses.losses_base import LossesBase
from ra2ce.analysis.losses.multi_link_losses import MultiLinkLosses
from ra2ce.analysis.losses.single_link_losses import SingleLinkLosses


class TestAnalysisOptionAnalysis:
    @pytest.mark.parametrize(
        "analysis_type, expected_analysis",
        [
            pytest.param(AnalysisDamagesEnum.DAMAGES, Damages, id="damages"),
            pytest.param(
                AnalysisLossesEnum.SINGLE_LINK_LOSSES,
                SingleLinkLosses,
                id="single_link_losses",
            ),
            pytest.param(
                AnalysisLossesEnum.MULTI_LINK_LOSSES,
                MultiLinkLosses,
                id="multi_link_losses",
            ),
        ],
    )
    def test_get_analysis_returns_tuple(
        self,
        analysis_type: AnalysisDamagesEnum | AnalysisLossesEnum,
        expected_analysis: type[Damages | LossesBase],
    ):
        # 1./2. Define test data./Run test.
        _result = AdaptationOptionAnalysis.get_analysis_info(analysis_type)

        # 3. Verify expectations.
        assert isinstance(_result, tuple)
        assert _result[0] == expected_analysis
        assert isinstance(_result[1], str)

    def test_get_analysis_raises_not_supported_error(self):
        # 1. Define test data.
        _analysis_type = "not supported"

        # 2. Run test.
        with pytest.raises(NotImplementedError) as exc:
            AdaptationOptionAnalysis.get_analysis_info(_analysis_type)

        # 3. Verify expectations.
        assert exc.match(f"Analysis {_analysis_type} not supported")

    @pytest.mark.parametrize(
        "analysis_type, col_name, match",
        [
            pytest.param(
                AnalysisDamagesEnum.DAMAGES, "dam_EV1_al", True, id="valid damages"
            ),
            pytest.param(
                AnalysisDamagesEnum.DAMAGES,
                "dam_EV1_al_segments",
                False,
                id="invalid damages",
            ),
            pytest.param(
                AnalysisLossesEnum.SINGLE_LINK_LOSSES,
                "vlh_EV1_me_total",
                True,
                id="valid losses",
            ),
            pytest.param(
                AnalysisLossesEnum.SINGLE_LINK_LOSSES,
                "vlh_business_EV1_me",
                False,
                id="invalid losses",
            ),
        ],
    )
    def test_get_result_column_based_on_regex(
        self,
        analysis_type: AnalysisDamagesEnum | AnalysisLossesEnum,
        col_name: str,
        match: bool,
    ):
        # 1. Define test data.
        _gdf = GeoDataFrame.from_dict({col_name: range(10)})
        _result_col = AdaptationOptionAnalysis.get_analysis_info(analysis_type)[1]
        _adaption_option_analysis = AdaptationOptionAnalysis(
            analysis_type=analysis_type,
            analysis_class=None,
            analysis_input=None,
            result_col=_result_col,
        )

        # 2. Run test.
        _result = _adaption_option_analysis.get_result_column(_gdf)

        # 3. Verify expectations.
        assert (_result.sum() > 0) == match

    @pytest.mark.parametrize(
        "analysis_type, expected_analysis",
        [
            pytest.param(AnalysisDamagesEnum.DAMAGES, Damages, id="damages"),
            pytest.param(
                AnalysisLossesEnum.SINGLE_LINK_LOSSES,
                SingleLinkLosses,
                id="single_link_losses",
            ),
            pytest.param(
                AnalysisLossesEnum.MULTI_LINK_LOSSES,
                MultiLinkLosses,
                id="multi_link_losses",
            ),
        ],
    )
    def test_from_config_returns_object(
        self,
        valid_adaptation_config: AnalysisConfigWrapper,
        analysis_type: AnalysisLossesEnum,
        expected_analysis: type[Damages | LossesBase],
    ):
        # 1. Define test data.
        _analysis_config = valid_adaptation_config
        assert _analysis_config.config_data.adaptation

        _analysis_config.config_data.adaptation.losses_analysis = analysis_type
        _id = _analysis_config.config_data.adaptation.adaptation_options[0].id

        # 2. Run test.
        _result = AdaptationOptionAnalysis.from_config(
            analysis_config=_analysis_config, analysis_type=analysis_type, option_id=_id
        )

        # 3. Verify expectations.
        assert isinstance(_result, AdaptationOptionAnalysis)
        assert _result.analysis_class == expected_analysis

    def test_execute_returns_series(self):
        class MockAnalysis(AnalysisBase, AnalysisProtocol):
            analysis: AnalysisConfigData.ANALYSIS_SECTION = None
            output_path: Path = None

            def __init__(self, *args) -> None:
                pass

            def execute(self):
                return self.generate_result_wrapper(
                    GeoDataFrame.from_dict(
                        {_col_name: range(10), "other_column": range(1, 11, 1)}
                    )
                )

        # 1. Define test data.
        _col_name = "result_column"
        _analysis = AdaptationOptionAnalysis(
            analysis_type=AnalysisDamagesEnum.DAMAGES,
            analysis_class=MockAnalysis,
            analysis_input=None,
            result_col="result.*",
        )

        # 2. Run test.
        _result = _analysis.execute(None)

        # 3. Verify expectations.
        assert isinstance(_result, Series)
        assert _result.sum() == 45
