from dataclasses import dataclass
from pathlib import Path

import pytest

from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionDamages,
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.direct.analysis_direct_protocol import AnalysisDirectProtocol
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol
from tests import test_data

_unsupported_direct_analysis = [
    AnalysisDamagesEnum.EFFECTIVENESS_MEASURES,
    AnalysisDamagesEnum.INVALID,
]
_unsupported_indirect_analysis = [AnalysisLossesEnum.INVALID]


class TestAnalysisCollection:
    @dataclass
    class MockAnalysisSectionDamages(AnalysisSectionDamages):
        analysis: AnalysisDamagesEnum = None

    @dataclass
    class MockAnalysisSectionLosses(AnalysisSectionLosses):
        analysis: AnalysisLossesEnum = None

    @pytest.fixture(autouse=False)
    def valid_analysis_ini(self) -> Path:
        _ini_file = test_data / "acceptance_test_data" / "analyses.ini"
        assert _ini_file.exists()
        return _ini_file

    def test_initialize(self):
        # 1./2. Define test data / Run test.
        _collection = AnalysisCollection(None, None)

        # 3. Verify expectations.
        assert isinstance(_collection, AnalysisCollection)
        assert _collection.damages_analyses is None
        assert _collection.losses_analyses is None

    def test_create_collection_with_no_analysis_returns_empty(self):
        # 1. Define test data.
        _config = AnalysisConfigWrapper()
        _config.config_data.analyses.append(None)

        # 2. Run test.
        _collection = AnalysisCollection.from_config(_config)

        # 3. Verify expectations.
        assert not any(_collection.damages_analyses)
        assert not any(_collection.losses_analyses)

    @pytest.mark.parametrize(
        "analysis",
        [
            pytest.param(_analysis_type)
            for _analysis_type in AnalysisDamagesEnum
            if _analysis_type not in _unsupported_direct_analysis
        ],
    )
    def test_create_collection_with_damages_analyses(
        self,
        analysis: AnalysisDamagesEnum,
    ):
        # 1. Define test data.
        _config = AnalysisConfigWrapper()
        _config.config_data.input_path = Path("Any path")
        _config.config_data.analyses.append(
            self.MockAnalysisSectionDamages(analysis=analysis)
        )

        # 2. Run test.
        _collection = AnalysisCollection.from_config(_config)

        # 3. Verify expectations.
        assert isinstance(_collection, AnalysisCollection)
        assert len(_collection.damages_analyses) == 1

        _generated_analysis = _collection.damages_analyses[0]
        assert isinstance(_generated_analysis, AnalysisDirectProtocol)
        assert _collection.damages_analyses[0].analysis.analysis == analysis

    @pytest.mark.parametrize(
        "analysis",
        [
            pytest.param(_analysis_type)
            for _analysis_type in AnalysisLossesEnum
            if _analysis_type not in _unsupported_indirect_analysis
        ],
    )
    def test_create_collection_with_losses_analyses(
        self,
        analysis: AnalysisLossesEnum,
    ):
        def verify_expectations(_collection, analysis):
            assert isinstance(_collection, AnalysisCollection)
            assert len(_collection.losses_analyses) == 1

            _generated_analysis = _collection.losses_analyses[0]
            assert isinstance(_generated_analysis, AnalysisLossesProtocol)
            assert _generated_analysis.analysis.analysis == analysis

        # 1. Define test data.
        _config = AnalysisConfigWrapper()
        _config.config_data.input_path = Path("Any input path")
        _config.config_data.output_path = Path("Any output path")
        _config.config_data.analyses.append(
            self.MockAnalysisSectionLosses(analysis=analysis)
        )

        if (
            analysis.config_value == "single_link_losses"
            or analysis.config_value == "multi_link_losses"
        ):
            with pytest.raises(ValueError):
                # 2. Run test.
                _collection = AnalysisCollection.from_config(_config)
                # 3. Verify expectations.
                verify_expectations(_collection, analysis)

        else:
            # 2. Run test.
            _collection = AnalysisCollection.from_config(_config)
            # 3. Verify expectations.
            verify_expectations(_collection, analysis)
