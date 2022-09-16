import pytest

from ra2ce.ra2ce_handler import Ra2ceInput
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
