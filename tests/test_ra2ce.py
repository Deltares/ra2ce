#!/usr/bin/env python

"""Tests for `ra2ce` package."""

import pathlib

import pytest

from click.testing import CliRunner

from ra2ce import ra2ce
from ra2ce import cli

import pandas as pd


def lookup_output(case='single_link_redundancy'):
    """Read an output file"""
    output_path = pathlib.Path('data/test/output')
    test_path = output_path / case / f'{case}_test.csv'
    return pd.read_csv(test_path)


@pytest.mark.skip(reason="work in progress")
def test_output():
    """Sample pytest test function for output"""
    case = 'single_link_redundancy'
    input_path = pathlib.Path('data/test/input') / case / 'network.ini'
    outputs_run = ra2ce.run(input_path)
    outputs_correct = lookup_output(case)
    assert outputs_run == outputs_correct, 'output should  be equal'


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'ra2ce.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
