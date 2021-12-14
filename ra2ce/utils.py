# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
@author: M. Kwant, Deltares
"""
# External modules
from configparser import ConfigParser
from pathlib import Path
import numpy as np
from ast import literal_eval
import codecs
import logging
from shutil import copyfile
import os
import sys

# Local modules
from .checks import input_validation, check_files, available_checks


list_indirect_analyses, list_direct_analyses = available_checks()


def parse_config(root, path=None, opt_cli=None):
    """Ajusted from HydroMT
    source: https://github.com/Deltares/hydromt/blob/af4e5d858b0ac0883719ca59e522053053c21b82/hydromt/cli/cli_utils.py"""
    opt = {}
    if path is not None and path.is_file():
        opt = configread(path, root, abs_path=False)  # Set from True to False 29-7-2021 by Frederique
        # make sure paths in config section are not abs paths
        if "setup_config" in opt:  # BELOW IS CURRENTLY NOT USED IN RA2CE BUT COULD BE GOOD FOR FUTURE LINKAGE WITH HYDROMT
            opt["setup_config"].update(configread(path).get("config", {}))
    elif path is not None:
        raise IOError(f"Config not found at {path}")
    if opt_cli is not None:  # BELOW IS CURRENTLY NOT USED IN RA2CE BUT COULD BE GOOD FOR FUTURE LINKAGE WITH HYDROMT
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


def configread(config_fn, root, encoding="utf-8", cf=None, defaults=dict(), noheader=False, abs_path=False):
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


def initiate_root_logger(filename):
    # Create a root logger and set the minimum logging level.

    logging.getLogger('').setLevel(logging.INFO)

    # Create a file handler and set the required logging level.
    fh = logging.FileHandler(filename=filename, mode='w')
    fh.setLevel(logging.INFO)
    
    # Create a console handler and set the required logging level.
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)  # Can be also set to WARNING

    # Create a formatter and add to the file and console handlers.
    formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add the file and console handlers to the root logger.
    logging.getLogger('').addHandler(fh)
    logging.getLogger('').addHandler(ch)


def configure_analyses(config):
    analyses_names = [a for a in config.keys() if 'analysis' in a]
    for a in analyses_names:
        if any(t in config[a]['analysis'] for t in list_direct_analyses):
            if 'direct' in config:
                (config['direct']).append(config[a])
            else:
                config['direct'] = [config[a]]
        elif any(t in config[a]['analysis'] for t in list_indirect_analyses):
            if 'indirect' in config:
                (config['indirect']).append(config[a])
            else:
                config['indirect'] = [config[a]]
        del config[a]

    return config


def load_config(root_path, config_path):
    # Read the configurations in network.ini and add the root path to the configuration dictionary.
    config_path = Path(config_path)
    if not config_path.is_file():
        config_path = root_path / config_path
    config = parse_config(root_path, path=config_path)
    config['project']['name'] = config_path.parts[-2]
    config['root_path'] = root_path
    
    # Validate the configuration input.
    config = input_validation(config)

    if config_path.stem == 'analyses':
        # Create a dictionary with direct and indirect analyses separately.
        config = configure_analyses(config)

    base_path = config_path.parent

    # Set the output paths in the configuration Dict for ease of saving to those folders.
    if config['project']['input_folder'] is not None:
        config['input'] = base_path / config['project']['input_folder']
    else:
        config['input'] = config['root_path'] / 'data' / config['project']['name'] / 'input'
    
    if config['project']['output_folder'] is not None:
        config['output'] = base_path / config['project']['output_folder']
    else:
        config['output'] = config['root_path'] / 'data' / config['project']['name'] / 'output'
    
    if config['project']['static_folder'] is not None:
        config['static'] = Path(config['project']['static_folder'])
    else:
        config['static'] = config['root_path'] / 'data' / config['project']['name'] / 'static'
        
    print('base path = '+ str(base_path))
    print('input path = '+ str(config['input']))
    print('output path = '+ str(config['output']))
    print('static path = '+ str(config['static']))

    # check if files exist:
    config = check_files(config)

    # copy ini file for future references to output folder
    copyfile(config_path, config['output'] / '{}.ini'.format(config_path.stem))
    return config
