# -*- coding: utf-8 -*-
"""
Created on 26-7-2021
"""
import codecs
import logging
import sys
from ast import literal_eval

# External modules
from configparser import ConfigParser
from pathlib import Path
from shutil import copyfile

import numpy as np

# Local modules
from .checks import available_checks, input_validation

list_indirect_analyses, list_direct_analyses = available_checks()


def get_root_path(net_ini: Path, ana_ini: Path) -> Path:
    def get_parent(ini_path: Path) -> Path:
        # Return the parent directory of the one containing the given file.
        if not ini_path:
            return None
        return ini_path.parent.parent

    _parents = list(
        set(
            [
                _parent_dir
                for _parent_dir in (map(get_parent, [net_ini, ana_ini]))
                if _parent_dir
            ]
        )
    )
    if not _parents:
        logging.error("No network.ini or analyses.ini supplied. Program will close.")
        sys.exit()
    if len(_parents) > 1:
        logging.error("Root directory differs between network and analyses .ini files")
        sys.exit()
    _root_path = _parents[0]
    if _root_path.is_dir():
        return _root_path
    else:
        logging.error(f"Path {_root_path} does not exist. Program will close.")
        sys.exit()


def parse_config(root: Path, path: Path = None, opt_cli=None) -> dict:
    """Ajusted from HydroMT
    source: https://github.com/Deltares/hydromt/blob/af4e5d858b0ac0883719ca59e522053053c21b82/hydromt/cli/cli_utils.py"""
    opt = {}
    if path is not None and path.is_file():
        opt = configread(
            path, root, abs_path=False
        )  # Set from True to False 29-7-2021 by Frederique
        # make sure paths in config section are not abs paths
        if (
            "setup_config" in opt
        ):  # BELOW IS CURRENTLY NOT USED IN RA2CE BUT COULD BE GOOD FOR FUTURE LINKAGE WITH HYDROMT
            opt["setup_config"].update(configread(path).get("config", {}))
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


def initiate_root_logger(filename: Path) -> None:
    # Create a root logger and set the minimum logging level.
    logging.getLogger("").setLevel(logging.INFO)

    # Create a file handler and set the required logging level.
    if not filename.is_file():
        if not filename.parent.is_dir():
            filename.parent.mkdir(parents=True)
        filename.touch()
    fh = logging.FileHandler(filename=filename, mode="w")
    fh.setLevel(logging.INFO)

    # Create a console handler and set the required logging level.
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)  # Can be also set to WARNING

    # Create a formatter and add to the file and console handlers.
    formatter = logging.Formatter(
        fmt="%(asctime)s - [%(filename)s:%(lineno)d] - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %I:%M:%S %p",
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add the file and console handlers to the root logger.
    logging.getLogger("").addHandler(fh)
    logging.getLogger("").addHandler(ch)


def configure_analyses(config: dict) -> dict:
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


def load_config(root_path: Path, config_path: str, check: bool = True) -> dict:
    # Read the configurations in network.ini and add the root path to the configuration dictionary.
    if not config_path.is_file():
        config_path = root_path / config_path
    config = parse_config(root_path, path=config_path)
    config["project"]["name"] = config_path.parts[-2]
    config["root_path"] = root_path

    if check:
        # Validate the configuration input.
        config = input_validation(config)

        if config_path.stem == "analyses":
            # Create a dictionary with direct and indirect analyses separately.
            config = configure_analyses(config)

        # Set the output paths in the configuration Dict for ease of saving to those folders.
        config["input"] = config["root_path"] / config["project"]["name"] / "input"
        config["static"] = config["root_path"] / config["project"]["name"] / "static"
        config["output"] = config["root_path"] / config["project"]["name"] / "output"

        if "hazard" in config:
            if "hazard_field_name" in config["hazard"]:
                if config["hazard"]["hazard_field_name"]:
                    config["hazard"]["hazard_field_name"] = config["hazard"][
                        "hazard_field_name"
                    ].split(",")

        # copy ini file for future references to output folder
        try:
            copyfile(config_path, config["output"] / "{}.ini".format(config_path.stem))
        except FileNotFoundError as e:
            logging.warning(e)
    return config


def get_files(config: dict) -> dict:
    """Checks if file of graph exist in network folder and adds filename to the files dict"""
    file_list = [
        "base_graph",
        "base_network",
        "origins_destinations_graph",
        "base_graph_hazard",
        "origins_destinations_graph_hazard",
        "base_network_hazard",
    ]
    files = {}
    for file in file_list:
        # base network is stored as feather object
        if file == "base_network" or file == "base_network_hazard":
            file_path = config["static"] / "output_graph" / "{}.feather".format(file)
        else:
            file_path = config["static"] / "output_graph" / "{}.p".format(file)

        # check if file exists, else return None
        if file_path.is_file():
            files[file] = file_path
            logging.info(f"Existing graph/network found: {file_path}.")
        else:
            files[file] = None
    return files
