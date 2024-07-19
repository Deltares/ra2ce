# This script is meant to postprocess the output
# generated during UQ3.

# This is the directory containing all the results generated
# in UQ3
from pathlib import Path

# This directory contains ALL the results for each of the hazards
# needs to be funneled into a postprocessing artifact.
_uq3_results = Path("/uq3_results")
assert _uq3_results.exists()
assert any(list(_uq3_results.rglob("*")))

# TODO: YOUR SCRIPT.


# Move (or generate) your results to be collected into s3 here
_postprocess_results = Path("/postprocess_result")
_postprocess_results.mkdir(parents=True, exist_ok=True)
