from typing import List

import pytest
from click.testing import CliRunner

from ra2ce import main
from tests import test_data

test_dir = test_data / "acceptance_test_data"


class TestMainCli:
    @pytest.mark.parametrize(
        "arguments, expected_error",
        [
            pytest.param(
                [
                    "--network_ini",
                    str(test_dir / "not_a_network.ini"),
                    "--analyses_ini",
                    str(test_dir / "analyses.ini"),
                ],
                str(test_dir / "not_a_network.ini"),
                id="Network is None",
            ),
            pytest.param(
                [
                    "--network_ini",
                    str(test_dir / "network.ini"),
                    "--analyses_ini",
                    str(test_dir / "not_an_analyses.ini"),
                ],
                str(test_dir / "not_an_analyses.ini"),
                id="Analyses is None",
            ),
        ],
    )
    def test_given_invalid_paths_raises_value_error(
        self, arguments: List[str], expected_error: str
    ):
        _run_result = CliRunner().invoke(
            main.run_analysis,
            arguments,
        )
        assert _run_result.exit_code == 1
        assert FileNotFoundError == type(_run_result.exc_info[1])
        assert expected_error == str(_run_result.exc_info[1])

    @pytest.mark.skip(reason="Still not clear which are the optional arguments.")
    def test_given_none_network_config_does_not_raise(self):
        _analysis_file = test_dir / "analyses.ini"
        assert _analysis_file.is_file()
        _run_result = CliRunner().invoke(
            main.run_analysis,
            ["--analyses_ini", str(_analysis_file)],
        )
        assert _run_result.exit_code == 0
        assert SystemExit == type(_run_result.exc_info[1])
