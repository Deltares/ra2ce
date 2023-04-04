"""
                    GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

    Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023 Stichting Deltares

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import logging
from pathlib import Path
from typing import Optional


class Ra2ceLogger:
    log_file: Optional[Path] = None

    def __init__(self, logging_dir: Path, logger_name: str) -> None:
        if not logging_dir.is_dir():
            logging_dir.mkdir(parents=True)
        self.log_file = logging_dir / f"{logger_name}.log"
        if not self.log_file.is_file():
            self.log_file.touch()

        self._set_file_handler()
        self._set_console_handler()
        self._set_formatter()
        logging.info(f"{logger_name} logger initialized.")

    def _get_logger(self) -> logging.Logger:
        """
        Gets the ra2ce logger which by default is the root logging.Logger.

        Returns:
            logging.Logger: Logger instance.
        """
        return logging.getLogger("")

    def _set_file_handler(self) -> None:
        # Create a root logger and set the minimum logging level.
        self._get_logger().setLevel(logging.INFO)
        self._file_handler = logging.FileHandler(filename=self.log_file, mode="a")
        self._file_handler.setLevel(logging.INFO)
        self._get_logger().addHandler(self._file_handler)

    def _set_console_handler(self) -> None:
        # Create a console handler and set the required logging level.
        self._console_handler = logging.StreamHandler()
        self._console_handler.setLevel(logging.INFO)  # Can be also set to WARNING
        self._get_logger().addHandler(self._console_handler)

    def _set_formatter(self) -> None:
        # Create a formatter and add to the file and console handlers.
        _formatter = logging.Formatter(
            fmt="%(asctime)s - [%(filename)s:%(lineno)d] - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %I:%M:%S %p",
        )
        self._file_handler.setFormatter(_formatter)
        self._console_handler.setFormatter(_formatter)
