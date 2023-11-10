import shutil

import pytest

from ra2ce.analyses.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    ProjectSection,
)
from ra2ce.analyses.analysis_config_data.readers.analysis_config_reader_base import (
    AnalysisConfigReaderBase,
)
from ra2ce.common.configuration.ini_configuration_reader_protocol import (
    ConfigDataReaderProtocol,
)
from tests import test_results


class TestAnalysisConfigReaderBase:
    @pytest.fixture(autouse=False)
    def valid_reader(self) -> AnalysisConfigReaderBase:
        _reader = AnalysisConfigReaderBase()
        assert isinstance(_reader, AnalysisConfigReaderBase)
        assert isinstance(_reader, ConfigDataReaderProtocol)
        return _reader

    def test_copy_output_files_no_file_doesnot_raise(
        self, valid_reader: AnalysisConfigReaderBase, request: pytest.FixtureRequest
    ):
        # 1. Define test data.
        _dir_name = "output"
        _config_data = AnalysisConfigData(
            root_path=test_results, project=ProjectSection(name=request.node.name)
        )
        _expected_dir = test_results / request.node.name / _dir_name
        if _expected_dir.exists():
            shutil.rmtree(_expected_dir)
        assert not _expected_dir.exists()
        _test_file = (
            test_results / request.node.name / "not_the_file_you_are_looking.for"
        )

        # 2. Run test.
        valid_reader._copy_output_files(_test_file, _config_data)

        # 3. Verify expectations.
        assert _expected_dir.exists()
        assert not _test_file.exists()

    def test_parse_path_list_non_existing_file(
        self, valid_reader: AnalysisConfigReaderBase, request: pytest.FixtureRequest
    ):
        # 1. Define test data.
        _config_data = AnalysisConfigData(
            root_path=test_results, project=ProjectSection(name=request.node.name)
        )
        _prop_name = "a_property"
        _path_list = "a"
        _expected_path = test_results / request.node.name / "input" / _prop_name / "a"

        # 2. Run test.
        _result = valid_reader._parse_path_list(_prop_name, _path_list, _config_data)

        # 3. Verify final expectations.
        assert isinstance(_result, list)
        assert len(_result) == 1
        assert _result[0] == _expected_path

    def test_parse_path_existing_file(
        self, valid_reader: AnalysisConfigReaderBase, request: pytest.FixtureRequest
    ):
        # 1. Define test data.
        _config_data = {
            "root_path": test_results,
            "project": {"name": request.node.name},
        }
        _prop_name = "a_property"
        _test_file_path = test_results / request.node.name / "made_up_file" / "a"

        # Create test files.
        if not _test_file_path.is_file():
            _test_file_path.parent.mkdir(parents=True)
            _test_file_path.touch(exist_ok=True)

        # 2. Run test.
        _result = valid_reader._parse_path_list(
            _prop_name, str(_test_file_path), _config_data
        )

        # 3. Verify final expectations.
        assert isinstance(_result, list)
        assert len(_result) == 1
        assert _result[0] == _test_file_path
        shutil.rmtree(_test_file_path.parent)
