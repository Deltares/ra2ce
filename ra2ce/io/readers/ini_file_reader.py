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


import codecs
from ast import literal_eval
from configparser import ConfigParser
from pathlib import Path

import numpy as np

from ra2ce.io.readers.file_reader_protocol import FileReaderProtocol


class IniFileReader(FileReaderProtocol):
    def read(self, ini_file: Path) -> dict:
        return self._parse_config(ini_file)

    def _parse_config(self, path: Path = None, opt_cli=None) -> dict:
        """Ajusted from HydroMT
        source: https://github.com/Deltares/hydromt/blob/af4e5d858b0ac0883719ca59e522053053c21b82/hydromt/cli/cli_utils.py"""
        opt = {}
        if path is not None and path.is_file():
            opt = self._configread(
                path, abs_path=False
            )  # Set from True to False 29-7-2021 by Frederique
            # make sure paths in config section are not abs paths
            if (
                "setup_config" in opt
            ):  # BELOW IS CURRENTLY NOT USED IN RA2CE BUT COULD BE GOOD FOR FUTURE LINKAGE WITH HYDROMT
                opt["setup_config"].update(self._configread(path).get("config", {}))
        elif path is not None:
            raise IOError(f"Config not found at {path}")
        if (
            opt_cli is not None
        ):  # BELOW IS CURRENTLY NOT USED IN RA2CE BUT COULD BE GOOD FOR FUTURE LINKAGE WITH HYDROMT
            for section in opt_cli:
                if not isinstance(opt_cli[section], dict):
                    raise ValueError(
                        "No section found in --opt values: "
                        "use <section>.<option>=<value> notation."
                    )
                if section not in opt:
                    opt[section] = opt_cli[section]
                    continue
                for option, value in opt_cli[section].items():
                    opt[section].update({option: value})
        return opt

    def _configread(
        self,
        config_fn,
        encoding="utf-8",
        cf=None,
        defaults=dict(),
        noheader=False,
        abs_path=False,
    ):
        """read model configuration from file and parse to dictionary

        Ajusted from HydroMT
        source: https://github.com/Deltares/hydromt/blob/af4e5d858b0ac0883719ca59e522053053c21b82/hydromt/config.py"""
        if cf is None:
            cf = ConfigParser(allow_no_value=True, inline_comment_prefixes=[";", "#"])

        cf.optionxform = str  # preserve capital letter
        with codecs.open(config_fn, "r", encoding=encoding) as fp:
            cf.read_file(fp)
        root = Path(config_fn.stem)
        cfdict = defaults.copy()
        for section in cf.sections():
            if section not in cfdict:
                cfdict[section] = dict()  # init
            sdict = dict()
            for key, value in cf.items(section):
                try:
                    v = literal_eval(value)
                    assert not isinstance(v, tuple)  # prevent tuples from being parsed
                    value = v
                except Exception:
                    pass
                if abs_path:
                    if isinstance(value, str) and root.joinpath(value).exists():
                        value = root.joinpath(value).resolve()
                    elif isinstance(value, list) and np.all(
                        [root.joinpath(v).exists() for v in value]
                    ):
                        value = [root.joinpath(v).resolve() for v in value]
                sdict[key] = value
            cfdict[section].update(**sdict)
        if noheader and "dummy" in cfdict:
            cfdict = cfdict["dummy"]

        return cfdict
