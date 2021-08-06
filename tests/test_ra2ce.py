#!/usr/bin/env python

"""Tests for `ra2ce` package."""

from pathlib import Path
import pytest

from click.testing import CliRunner

from ra2ce import ra2ce
# from ra2ce import cli

import pandas as pd


def lookup_output(case='single_link_redundancy'):
    """Read an output file"""
    output_path = Path('data/test/output')
    test_path = output_path / case / f'{case}_test.csv'
    return pd.read_csv(test_path)


# @pytest.mark.skip(reason="work in progress")
def test_output():
    """Sample pytest test function for output"""
    case = 'single_link_redundancy'
    input_network_path = Path('data/test/network.ini')
    input_analyses_path = Path('data/test/analyses.ini')
    outputs_run = ra2ce.main(input_network_path, input_analyses_path)
    outputs_correct = lookup_output(case)
    assert outputs_run == outputs_correct, 'output should  be equal'


@pytest.mark.skip(reason="work in progress")
def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'ra2ce.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
