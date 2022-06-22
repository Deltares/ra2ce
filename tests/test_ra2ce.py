#!/usr/bin/env python

"""Tests for `ra2ce` package."""

from ra2ce import __version__
from pathlib import Path

TESTDATADIR = Path(__file__).resolve().parent.joinpath("data")


def get_paths(name):
    network_conf = TESTDATADIR / name / 'network.ini'
    analyses_conf = TESTDATADIR / name / 'analyses.ini'
    if not network_conf.is_file():
        network_conf = None
    if not analyses_conf.is_file():
        analyses_conf = None
    return network_conf, analyses_conf


def get_output_graph_path(name):
    return TESTDATADIR / name / 'static' / 'output_graph'


def check_output_graph_files(name, file_names):
    folder = get_output_graph_path(name)
    for fn in file_names:
        assert folder.joinpath(fn).is_file()


def get_output_path(name):
    return TESTDATADIR / name / 'output'


def check_output_files(name, analysis_name, file_names):
    folder = get_output_path(name)
    for fn in file_names:
        assert folder.joinpath(analysis_name, fn).is_file()


def test_version():
    assert __version__ == "0.1.0"


def test_import():
    """Import test"""
    try:
        from ra2ce.ra2ce import main
    except ImportError:
        raise
