from dataclasses import dataclass
from pathlib import Path

import pytest

from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionDirect,
    AnalysisSectionIndirect,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_direct_enum import (
    AnalysisDirectEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_indirect_enum import (
    AnalysisIndirectEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.direct.analysis_direct_protocol import AnalysisDirectProtocol
from ra2ce.analysis.indirect.analysis_indirect_protocol import AnalysisIndirectProtocol
from tests import test_data

_unsupported_direct_analysis = [
    AnalysisDirectEnum.EFFECTIVENESS_MEASURES,
    AnalysisDirectEnum.INVALID,
]
_unsupported_indirect_analysis = [AnalysisIndirectEnum.INVALID]


class TestAnalysisCollection:
    @dataclass
    class MockAnalysisSectionDirect(AnalysisSectionDirect):
        analysis: AnalysisDirectEnum = None

    @dataclass
    class MockAnalysisSectionIndirect(AnalysisSectionIndirect):
        analysis: AnalysisIndirectEnum = None

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
        assert _collection.direct_analyses is None
        assert _collection.indirect_analyses is None

    def test_create_collection_with_no_analysis_returns_empty(self):
        # 1. Define test data.
        _config = AnalysisConfigWrapper()
        _config.config_data.analyses.append(None)

        # 2. Run test.
        _collection = AnalysisCollection.from_config(_config)

        # 3. Verify expectations.
        assert not any(_collection.direct_analyses)
        assert not any(_collection.indirect_analyses)

    @pytest.mark.parametrize(
        "analysis",
        [
            pytest.param(_analysis_type)
            for _analysis_type in AnalysisDirectEnum
            if _analysis_type not in _unsupported_direct_analysis
        ],
    )
    def test_create_collection_with_direct_analyses(
        self,
        analysis: AnalysisDirectEnum,
    ):
        # 1. Define test data.
        _config = AnalysisConfigWrapper()
        _config.config_data.input_path = Path("Any path")
        _config.config_data.analyses.append(
            self.MockAnalysisSectionDirect(analysis=analysis)
        )

        # 2. Run test.
        _collection = AnalysisCollection.from_config(_config)

        # 3. Verify expectations.
        assert isinstance(_collection, AnalysisCollection)
        assert len(_collection.direct_analyses) == 1

        _generated_analysis = _collection.direct_analyses[0]
        assert isinstance(_generated_analysis, AnalysisDirectProtocol)
        assert _collection.direct_analyses[0].analysis.analysis == analysis

    @pytest.mark.parametrize(
        "analysis",
        [
            pytest.param(_analysis_type)
            for _analysis_type in AnalysisIndirectEnum
            if _analysis_type not in _unsupported_indirect_analysis
        ],
    )
    def test_create_collection_with_indirect_analyses(
        self,
        analysis: AnalysisIndirectEnum,
    ):
        # 1. Define test data.
        _config = AnalysisConfigWrapper()
        _config.config_data.input_path = Path("Any input path")
        _config.config_data.output_path = Path("Any output path")
        _config.config_data.analyses.append(
            self.MockAnalysisSectionIndirect(analysis=analysis)
        )

        # 2. Run test.
        _collection = AnalysisCollection.from_config(_config)

        # 3. Verify expectations.
        assert isinstance(_collection, AnalysisCollection)
        assert len(_collection.indirect_analyses) == 1

        _generated_analysis = _collection.indirect_analyses[0]
        assert isinstance(_generated_analysis, AnalysisIndirectProtocol)
        assert _generated_analysis.analysis.analysis == analysis
