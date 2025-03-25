from dataclasses import dataclass
from pathlib import Path
from typing import Type

import pytest

from ra2ce.analysis.adaptation.adaptation import Adaptation
from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionAdaptation,
    AnalysisSectionDamages,
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_enum import AnalysisEnum
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_protocol import AnalysisProtocol
from ra2ce.analysis.damages.analysis_damages_protocol import AnalysisDamagesProtocol
from ra2ce.analysis.damages.damages import Damages
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol
from ra2ce.analysis.losses.losses_base import LossesBase


class TestAnalysisCollection:
    @dataclass
    class MockAnalysisSectionDamages(AnalysisSectionDamages):
        analysis: AnalysisDamagesEnum = None

    @dataclass
    class MockAnalysisSectionLosses(AnalysisSectionLosses):
        analysis: AnalysisLossesEnum = None

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
            for _analysis_type in AnalysisDamagesEnum.list_valid_options()
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
        assert isinstance(_generated_analysis, AnalysisDamagesProtocol)
        assert _collection.damages_analyses[0].analysis.analysis == analysis

    @pytest.mark.parametrize(
        "analysis",
        [
            pytest.param(_analysis_type)
            for _analysis_type in AnalysisLossesEnum.list_valid_options()
        ],
    )
    def test_create_collection_with_losses_analyses(
        self,
        analysis: AnalysisLossesEnum,
    ):
        # 1. Define test data.
        _config = AnalysisConfigWrapper()
        _config.config_data.input_path = Path("Any input path")
        _config.config_data.output_path = Path("Any output path")
        _config.config_data.analyses.append(
            self.MockAnalysisSectionLosses(analysis=analysis)
        )

        # 2. Run test.
        _collection = AnalysisCollection.from_config(_config)

        # 3. Verify expectations.
        assert isinstance(_collection, AnalysisCollection)
        assert len(_collection.losses_analyses) == 1

        _generated_analysis = _collection.losses_analyses[0]
        assert isinstance(_generated_analysis, AnalysisLossesProtocol)
        assert _generated_analysis.analysis.analysis == analysis

    def test_create_collection_with_adaptation(self):
        # 1. Define test data.
        _config = AnalysisConfigWrapper()
        _config.config_data.input_path = Path("Any path")
        _config.config_data.analyses.append(
            AnalysisSectionAdaptation(analysis=AnalysisEnum.ADAPTATION)
        )

        # 2. Run test.
        _collection = AnalysisCollection.from_config(_config)

        # 3. Verify expectations.
        assert isinstance(_collection, AnalysisCollection)
        assert (
            _collection.adaptation_analysis.analysis.analysis == AnalysisEnum.ADAPTATION
        )
