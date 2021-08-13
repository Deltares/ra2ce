#!/usr/bin/env python

"""Tests for `ra2ce` package."""

from pathlib import Path
import pytest
from click.testing import CliRunner
import pandas as pd
from ra2ce import ra2ce


def lookup_output(output_path, case):
    """Read an output file"""
    root_path = Path(__file__).resolve().parent.parent
    test_path = Path(output_path) / case / f'{case}_test.csv'
    if not test_path.is_file():
        test_path = root_path / test_path
    return pd.read_csv(test_path)


def test_output():
    """Sample pytest test function for output"""
    cases = ['direct', 'single_link_redundancy', 'multi_link_redundancy', 'optimal_route_origin_destination',
             'multi_link_origin_destination']
    input_network_path = Path('data/test/network.ini')
    input_analyses_path = Path('data/test/analyses.ini')
    ra2ce.main(input_network_path, input_analyses_path)

    # to_check = ['ra2ce_fid', 'alt_dist', 'alt_nodes', 'diff_dist']

    for case in cases:
        outputs_correct = lookup_output('data/test/output/correct', case)
        outputs_test = lookup_output('data/test/output', case)

        # Check if the pandas dataframes are equal in all aspects
        print(case)
        pd.testing.assert_frame_equal(outputs_test, outputs_correct)


@pytest.mark.skip(reason="work in progress")
def test_command_line_interface():
    """Test the CLI."""
    from ra2ce import cli

    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'ra2ce.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
