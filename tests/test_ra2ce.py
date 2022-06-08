#!/usr/bin/env python

"""Tests for `ra2ce` package."""

from ra2ce import __version__
from pathlib import Path

TESTDATADIR = Path(__file__).resolve().parent.joinpath("data")


def get_paths(name):
    print(TESTDATADIR)
    network_conf = TESTDATADIR / name / 'network.ini'
    analyses_conf = TESTDATADIR / name / 'analyses.ini'
    print(network_conf)
    if not network_conf.is_file():
        network_conf = None
    if not analyses_conf.is_file():
        analyses_conf = None
    return network_conf, analyses_conf


# def check_output_files():



def test_version():
    assert __version__ == "0.1.0"


def test_import():
    """Import test"""
    try:
        from ra2ce.ra2ce import main
    except ImportError:
        raise
