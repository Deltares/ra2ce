from pathlib import Path

import pytest
from geopandas import GeoDataFrame
from shapely import Point

from ra2ce.analysis.adaptation.adaptation_option_analysis import (
    AdaptationOptionAnalysis,
)
from ra2ce.analysis.adaptation.adaptation_option_partial_result import (
    AdaptationOptionPartialResult,
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
    def test_get_analysis_info_returns_tuple(
        self,
        analysis_type: AnalysisDamagesEnum | AnalysisLossesEnum,
        expected_analysis: type[Damages | LossesBase],
    ):
        # 1./2. Define test data./Run test.
        _result = AdaptationOptionAnalysis.get_analysis_info(analysis_type)

        # 3. Verify expectations.
        assert isinstance(_result, tuple)
        assert _result[0] == expected_analysis
        assert all(isinstance(x, str) for x in _result[1:])

    def test_get_analysis_info_raises_not_supported_error(self):
        # 1. Define test data.
        _analysis_type = "not supported"

        # 2. Run test.
        with pytest.raises(NotImplementedError) as exc:
            AdaptationOptionAnalysis.get_analysis_info(_analysis_type)

        # 3. Verify expectations.
        assert exc.match(f"Analysis {_analysis_type} not supported")

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

    def test_execute_returns_result(self):
        class MockAnalysis(AnalysisBase, AnalysisProtocol):
            analysis: AnalysisConfigData.ANALYSIS_SECTION = None
            output_path: Path = None

            def __init__(self, *args) -> None:
                pass

            def execute(self):
                return self.generate_result_wrapper(
                    GeoDataFrame.from_dict(
                        {
                            _id_col: range(10),
                            "geometry": [Point(x, 0) for x in range(10)],
                            "result_column": range(1, 11, 1),
                            "other_column": range(2, 12, 1),
                        }
                    )
                )

        # 1. Define test data.
        _option_id = "Option1"
        _id_col = "link_id"
        _analysis_type = AnalysisDamagesEnum.DAMAGES
        _analysis = AdaptationOptionAnalysis(
            option_id=_option_id,
            analysis_type=_analysis_type,
            analysis_class=MockAnalysis,
            analysis_input=None,
            result_col="result.*",
        )

        # 2. Run test.
        _result = _analysis.execute(None)

        # 3. Verify expectations.
        assert isinstance(_result, AdaptationOptionPartialResult)
        assert _result.data_frame[
            f"{_option_id}_{_analysis_type.config_value}"
        ].sum() == pytest.approx(55)
