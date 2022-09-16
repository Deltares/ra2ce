import shutil

import pytest

from ra2ce.ra2ce_handler import Ra2ceHandler, Ra2ceInput
from tests import test_data


class TestRefactorings:
    @pytest.mark.skip(reason="work in progress")
    def test_given_input_gets_configurations(self):
        root_test_dir = test_data / "acceptance_test_data"
        _network_ini = root_test_dir / "network.ini"
        _analysis_ini = root_test_dir / "analyses.ini"
        assert _network_ini.is_file()
        assert _analysis_ini.is_file()

        _race_input = Ra2ceInput(_network_ini, _analysis_ini)

        assert _race_input.validate_input()
        assert _race_input.network

    @pytest.mark.skip(reason="work in progress")
    def test_1_1_given_only_network_shape_redundancy(self):
        """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
        # 1. Given test data
        test_name = "1_1_network_shape_redundancy"
        _test_dir = test_data / test_name
        network_ini = _test_dir / "network.ini"
        analysis_ini = _test_dir / "analyses.ini"
        assert network_ini.is_file()
        assert analysis_ini.is_file()
        # Purge output dirs.
        _output_graph_dir = _test_dir / "static" / "output_graph"
        _output_files_dir = _test_dir / "output"

        shutil.rmtree(_output_graph_dir, ignore_errors=True)
        shutil.rmtree(_output_files_dir, ignore_errors=True)

        _expected_analysis_output_files = [
            _output_files_dir
            / "single_link_redundancy"
            / "single_link_redundancy_test.csv"
        ]

        # 2. When test:
        Ra2ceHandler(network_ini, analysis_ini)

        # 3. Then, validate expectations
        _expected_graph_files = [
            "1_1_network_shape_redundancy_lines_that_merged.shp",
            "base_graph.p",
            "base_network.feather",
        ]
        for _graph_file in _expected_graph_files:
            _graph_file = _output_graph_dir / _graph_file
            assert _graph_file.is_file() and _graph_file.exists()
        for _analysis_output in _expected_analysis_output_files:
            assert _analysis_output.is_file() and _analysis_output.exists()
