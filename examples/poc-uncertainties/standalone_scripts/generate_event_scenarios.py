import json
import random
from pathlib import Path

import boto3

# s3://ra2ce-data/uncertainty_hackathon/flood_maps/
bucket = "ra2ce-data"
_root_dir = "uncertainty_hackathon/output_1/"

client = boto3.client("s3")
result = client.list_objects(Bucket=bucket, Prefix=_root_dir, Delimiter="/")
_selected_events = []
n_runs = 100
for _sub_prefix in result.get("CommonPrefixes"):
    _prefix = _sub_prefix["Prefix"]
    _prefix_path = Path(_prefix)
    _prefix_result = client.list_objects(Bucket=bucket, Prefix=_prefix, Delimiter="/")
    _event_files = [
        str(
            (Path(_c["Prefix"]).joinpath("output_graph")).relative_to(
                _prefix_path.parent
            )
        )
        for _c in _prefix_result.get("CommonPrefixes")
    ]
    for n in range(n_runs):
        _selected_events.append(random.choice(_event_files))
print(json.dumps(_selected_events))
