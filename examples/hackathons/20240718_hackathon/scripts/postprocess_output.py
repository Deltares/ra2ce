# This script is meant to postprocess the output
# generated during UQ3.

# This is the directory containing all the results generated
# in UQ3
from pathlib import Path

# This directory contains ALL the results for each of the hazards
# needs to be funneled into a postprocessing artifact.
_uq3_results = Path("/uq3_results")
# Uncomment this once we have real output results data stored in the s3
assert _uq3_results.exists()
assert any(list(_uq3_results.rglob("*")))

# Move (or generate) your results to be collected into s3 here
_postprocess_results = Path("/postprocess_result")
_postprocess_results.mkdir(parents=True, exist_ok=True)

# TODO: REPLACE WITH THE REAL POSTPROCESSING SCRIPT.
_found_files = []
if _uq3_results.exists():
    _found_files = list(_uq3_results.rglob("*"))

if not any(_found_files):
    _dummy_message = (
        "No files found in `/uq3_results`, did you generate uq3 data in the s3?"
    )
    print(_dummy_message)
    _found_files = [_dummy_message]

_dummy_result_file = _postprocess_results.joinpath("dummy_result.txt")
_dummy_result_file.write_text("\n".join(list(map(str, _found_files))), encoding="utf-8")
