import shutil
from pathlib import Path
from turtle import st

import pytest

from ra2ce.network.graph_files.graph_files_collection import GraphFilesCollection
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.network_config_data import (
    NetworkConfigData,
    NetworkSection,
)
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper
from tests import test_data, test_results


class TestNetworkConfigWrapper:
    @pytest.fixture(name="test_case_dir")
    def _get_test_case_dir(self, request: pytest.FixtureRequest) -> Path:
        _test_case_dir = test_results.joinpath(request.node.originalname)
        if request.node.originalname != request.node.name:
            _test_case_dir = _test_case_dir.joinpath(
                request.node.name.split("[")[-1].split("]")[0].lower().replace(" ", "_")
            )
        return _test_case_dir

    def test_from_data_without_output_graph_does_not_raise(self):
        # 1. Define test data
        _network_config = NetworkConfigData(
            root_path=Path("dummy_path"),
            static_path=None,
        )

        # 2. Run test
        _ = NetworkConfigWrapper.from_data(None, _network_config)

    def test_from_data_with_output_graph_creates_dir(self, test_case_dir: Path):
        # 1. Define test data
        _network_config = NetworkConfigData(
            root_path=Path("dummy_path"),
            static_path=test_case_dir.joinpath("static"),
        )
        _output_graph_dir = _network_config.output_graph_dir
        assert _output_graph_dir
        if _output_graph_dir.exists():
            shutil.rmtree(_output_graph_dir)

        # 2. Run test
        _ = NetworkConfigWrapper.from_data(None, _network_config)

        # 3. Verify expectations.
        assert _output_graph_dir.exists()

    @pytest.mark.parametrize(
        "reuse_existing_network",
        [
            pytest.param(True, id="Reuse existing network"),
            pytest.param(False, id="Do not reuse existing network"),
        ],
    )
    def test_from_data_wipes_output_graph_based_on_reuse(
        self,
        test_case_dir: Path,
        reuse_existing_network: bool,
    ):
        # 1. Define test data
        _reference_dir = test_data.joinpath("simple_inputs")
        assert _reference_dir.exists()

        if test_case_dir.exists():
            shutil.rmtree(test_case_dir)
        test_case_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(_reference_dir, test_case_dir)

        _network_config = NetworkConfigData(
            root_path=Path("dummy_path"),
            static_path=test_case_dir.joinpath("static"),
            network=NetworkSection(
                reuse_network_output=reuse_existing_network,
            ),
        )

        _graph_file = (_network_config.output_graph_dir).joinpath("base_graph.p")
        assert _graph_file.is_file()

        # 2. Run test
        _ = NetworkConfigWrapper.from_data(None, _network_config)

        # 3. Verify expectations.
        assert _graph_file.is_file() == reuse_existing_network

    def test_read_graphs_from_config_without_output_dir_raises(
        self, request: pytest.FixtureRequest
    ):
        # 1. Define test data
        _test_dir = test_results / request.node.name
        if _test_dir.exists():
            shutil.rmtree(_test_dir)

        # 2. Run test
        with pytest.raises(ValueError) as exc_err:
            NetworkConfigWrapper.read_graphs_from_config(_test_dir)

        # 3. Verify expectations.
        assert str(exc_err.value) == "Path does not exist: {}".format(_test_dir)

    def test_read_graphs_with_existing_dir_without_files(
        self, request: pytest.FixtureRequest
    ):
        # 1. Define test data
        _test_dir = test_results / request.node.name
        if not _test_dir.exists():
            _test_dir.mkdir(parents=True)

        # 2. Run test.
        _result = NetworkConfigWrapper.read_graphs_from_config(_test_dir)

        # 3. Verify expectations
        assert isinstance(_result, GraphFilesCollection)
        assert _result.base_graph.graph is None
        assert _result.base_graph_hazard.graph is None
        assert _result.origins_destinations_graph.graph is None
        assert _result.origins_destinations_graph_hazard.graph is None
        assert _result.base_network.graph is None
        assert _result.base_network_hazard.graph is None
        shutil.rmtree(_test_dir)

    def test_analysis_config_wrapper_valid_without_ini_file(self):
        # 1. Define test data
        _network_wrapper = NetworkConfigWrapper()
        _network_wrapper.config_data = NetworkConfigData(
            root_path=Path("dummy_path"),
            static_path=Path("dummy_path"),
        )
        _network_wrapper.config_data.network.source = SourceEnum.OSB_BPF
        _network_wrapper.ini_file = None

        # 2. Run test.
        _result = _network_wrapper.is_valid()

        # 3. Verify expectations.
        assert _result is True
