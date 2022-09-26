import logging
import shutil
from pathlib import Path
from typing import List

import pytest

from ra2ce.ra2ce_logging import Ra2ceLogger
from tests import test_results


def get_logged_text_lines(log_file: Path) -> List[str]:
    _logged_text = log_file.read_text()
    assert _logged_text
    return _logged_text.splitlines(keepends=False)


class TestRa2ceLogging:
    def test_given_non_existent_dir_creates_log(self, request: pytest.FixtureRequest):
        _test_dir = test_results / request.node.name
        _logger_name = "testlog"
        shutil.rmtree(_test_dir, ignore_errors=True)
        _initial_log_mssg = f"{_logger_name} logger initialized."

        assert not _test_dir.is_dir()

        _logger = Ra2ceLogger(_test_dir, _logger_name)

        assert logging.getLogger("") == _logger._get_logger()
        assert _test_dir.is_dir()
        assert _logger.log_file.is_file()
        assert _logger.log_file.suffix == ".log"
        assert _logger.log_file.stem == _logger_name
        _logged_lines = get_logged_text_lines(_logger.log_file)
        assert len(_logged_lines) == 1
        assert _initial_log_mssg in _logged_lines[0]

    def test_log_messages(self, request: pytest.FixtureRequest):
        # 1. Define test data.
        _test_dir = test_results / request.node.name
        _logger_name = "testlog"
        _err_mssg = "Minim cupidatat cupidatat ullamco mollit enim consequat proident incididunt excepteur amet."
        _warn_mssg = "Culpa eu et ea qui mollit tempor nulla consequat ex incididunt elit aliqua."
        _info_mssg = "Commodo elit aliqua amet velit."

        shutil.rmtree(_test_dir, ignore_errors=True)

        assert not _test_dir.is_dir()

        # 2. Run test
        _logger = Ra2ceLogger(_test_dir, _logger_name)
        logging.error(_err_mssg)
        logging.warning(_warn_mssg)
        logging.info(_info_mssg)

        # 3. Verify final expectations.
        assert _logger.log_file.exists()
        _logged_lines = get_logged_text_lines(_logger.log_file)
        assert len(_logged_lines) >= 4
        assert _err_mssg in _logged_lines[1]
        assert _warn_mssg in _logged_lines[2]
        assert _info_mssg in _logged_lines[3]
