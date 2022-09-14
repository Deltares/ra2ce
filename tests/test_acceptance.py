from ra2ce.ra2ce import main
from tests import test_data


class TestAcceptance:
    def test_ra2ce_package_can_be_imported(self):
        """Import test"""
        try:
            from ra2ce.ra2ce import main
        except ImportError:
            raise

    def test_given_test_data_main_does_not_throw(self):
        _test_dir = test_data / "acceptance_test_data"
        _network = _test_dir / "network.ini"
        _analysis = _test_dir / "analyses.ini"

        assert _network.is_file()
        assert _analysis.is_file()

        main(_network, _analysis)
