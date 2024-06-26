import pytest

from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.losses.weighing_analysis.weighing_analysis_factory import (
    WeighingAnalysisFactory,
)
from ra2ce.analysis.losses.weighing_analysis.weighing_analysis_protocol import (
    WeighingAnalysisProtocol,
)

_unsupported_enums = [WeighingEnum.NONE, WeighingEnum.INVALID]


class TestWeighingAnalysisFactory:
    @pytest.mark.parametrize(
        "valid_enum",
        [pytest.param(we) for we in WeighingEnum if we not in _unsupported_enums],
    )
    def test_get_analysis_with_valid_enum(self, valid_enum: WeighingEnum):
        _analysis = WeighingAnalysisFactory.get_analysis(valid_enum)

        assert isinstance(_analysis, WeighingAnalysisProtocol)

    @pytest.mark.parametrize(
        "valid_enum",
        [pytest.param(we) for we in _unsupported_enums],
    )
    def test_get_analysis_with_unsupported_enum(self, valid_enum: WeighingEnum):
        # 2. Run test.
        with pytest.raises(NotImplementedError) as exc_err:
            WeighingAnalysisFactory.get_analysis(valid_enum)

        # 3. Verify expectations.
        assert str(exc_err.value) == "Weighing type {} not yet supported.".format(
            valid_enum
        )

    def test_get_analysis_with_unknown_enum(self):
        # 1. Define test data.
        _invalid_enum = "NotAnEnum"

        # 2. Run test.
        with pytest.raises(NotImplementedError) as exc_err:
            WeighingAnalysisFactory.get_analysis(_invalid_enum)

        # 3. Verify expectations.
        assert str(exc_err.value) == "Weighing type {} not yet supported.".format(
            _invalid_enum
        )
