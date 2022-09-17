import codecs
import logging
from ast import literal_eval
from configparser import ConfigParser
from pathlib import Path
from shutil import copyfile

import numpy as np

from ra2ce.io.ra2ce_io_validator import available_checks, input_validation

list_indirect_analyses, list_direct_analyses = available_checks()


class IniConfigurationReader:
    """
    Generic Ini Configuration Reader.
    Eventually it will be split into smaller readers for each type of IniConfiguration.
    """

    def configure_analyses(self, config: dict) -> dict:
        analyses_names = [a for a in config.keys() if "analysis" in a]
        for a in analyses_names:
            if any(t in config[a]["analysis"] for t in list_direct_analyses):
                if "direct" in config:
                    (config["direct"]).append(config[a])
                else:
                    config["direct"] = [config[a]]
            elif any(t in config[a]["analysis"] for t in list_indirect_analyses):
                if "indirect" in config:
                    (config["indirect"]).append(config[a])
                else:
                    config["indirect"] = [config[a]]
            del config[a]

        return config

    def import_configuration(
        self, root_path: Path, config_path: str, check: bool = True
    ) -> dict:
        # Read the configurations in network.ini and add the root path to the configuration dictionary.
        if not config_path.is_file():
            config_path = root_path / config_path
        config = self.parse_config(root_path, path=config_path)
        config["project"]["name"] = config_path.parts[-2]
        config["root_path"] = root_path

        if check:
            # Validate the configuration input.
            config = input_validation(config)

            if config_path.stem == "analyses":
                # Create a dictionary with direct and indirect analyses separately.
                config = self.configure_analyses(config)

            # Set the output paths in the configuration Dict for ease of saving to those folders.
            config["input"] = config["root_path"] / config["project"]["name"] / "input"
            config["static"] = (
                config["root_path"] / config["project"]["name"] / "static"
            )
            # config["output"] = config["root_path"] / config["project"]["name"] / "output"

            if "hazard" in config:
                if "hazard_field_name" in config["hazard"]:
                    if config["hazard"]["hazard_field_name"]:
                        config["hazard"]["hazard_field_name"] = config["hazard"][
                            "hazard_field_name"
                        ].split(",")

            # copy ini file for future references to output folder
            def create_config_dir(dir_name: str):
                _dir = config["root_path"] / config["project"]["name"] / dir_name
                if not _dir.exists():
                    _dir.mkdir(parents=True)
                config[dir_name] = _dir

            # create_config_dir("static")
            create_config_dir("output")

            try:
                copyfile(
                    config_path, config["output"] / "{}.ini".format(config_path.stem)
                )
            except FileNotFoundError as e:
                logging.warning(e)
        return config

    def parse_config(self, root: Path, path: Path = None, opt_cli=None) -> dict:
        """Ajusted from HydroMT
        source: https://github.com/Deltares/hydromt/blob/af4e5d858b0ac0883719ca59e522053053c21b82/hydromt/cli/cli_utils.py"""
        opt = {}
        if path is not None and path.is_file():
            opt = self.configread(
                path, root, abs_path=False
            )  # Set from True to False 29-7-2021 by Frederique
            # make sure paths in config section are not abs paths
            if (
                "setup_config" in opt
            ):  # BELOW IS CURRENTLY NOT USED IN RA2CE BUT COULD BE GOOD FOR FUTURE LINKAGE WITH HYDROMT
                opt["setup_config"].update(self.configread(path).get("config", {}))
        elif path is not None:
            raise IOError(f"Config not found at {path}")
        if (
            opt_cli is not None
        ):  # BELOW IS CURRENTLY NOT USED IN RA2CE BUT COULD BE GOOD FOR FUTURE LINKAGE WITH HYDROMT
            for section in opt_cli:
                if not isinstance(opt_cli[section], dict):
                    raise ValueError(
                        f"No section found in --opt values: "
                        "use <section>.<option>=<value> notation."
                    )
                if section not in opt:
                    opt[section] = opt_cli[section]
                    continue
                for option, value in opt_cli[section].items():
                    opt[section].update({option: value})
        return opt

    def configread(
        self,
        config_fn,
        root,
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
