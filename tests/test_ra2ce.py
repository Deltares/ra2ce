#!/usr/bin/env python

"""Tests for `ra2ce` package."""

from pathlib import Path
import pytest

from click.testing import CliRunner

from ra2ce import ra2ce
# from ra2ce import cli

import pandas as pd


def lookup_output(output_path=Path('data/test/output/correct'), case='single_link_redundancy'):
    """Read an output file"""
    test_path = output_path / case / f'{case}_test.csv'
    return pd.read_csv(test_path)


# @pytest.mark.skip(reason="work in progress")
def test_output():
    """Sample pytest test function for output"""
    cases = ['single_link_redundancy', 'multi_link_redundancy', 'optimal_route_origin_destination',
             'multi_link_origin_destination']
    input_network_path = Path('data/test/network.ini')
    input_analyses_path = Path('data/test/analyses.ini')
    ra2ce.main(input_network_path, input_analyses_path)

    for case in cases:
        outputs_correct = lookup_output(case)
        outputs_test = lookup_output(Path('data/test/output'), case)

        # Check if the pandas dataframes are equal in all aspects
        pd.testing.assert_frame_equal(outputs_test, outputs_correct)


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
