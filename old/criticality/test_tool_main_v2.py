import pytest
import tool_main_v2, user_input_v2, network_functions_v2
import os
from pathlib import Path
import filecmp

input_folder = Path('GIS/input')
output_folder = Path('GIS/output')
input_values = ['.', 'o', 'e', 'test_shp_singlelink', 'test_shp_singlelink', 'n', 'y,']
output = []

def mock_input(s):
    output.append(s)
    return input_values.pop(0)

tool_main_v2.input = mock_input
user_input_v2.input = mock_input
network_functions_v2.input = mock_input

@pytest.fixture(scope='module')
def run():
    tool_main_v2.main()

@pytest.mark.parametrize('extension', ['cpg', 'dbf', 'prj', 'shp', 'shx'])
def test_shp_singlelink(run, extension):
    ref_files = (output_folder / Path('ref_shp_singlelink')).glob('*.{}'.format(extension))
    test_files = output_folder.glob('*.{}'.format(extension))

    for ref_file, test_file in zip(ref_files, test_files):
        assert filecmp.cmp(test_file, ref_file)
        os.remove(test_file)
