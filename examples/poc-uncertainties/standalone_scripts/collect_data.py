import json
from pathlib import Path

import boto3

# s3://ra2ce-data/hackathon_uncertainty/flood_maps/
bucket = "ra2ce-data"
_root_dir = "hackathon_uncertainty/flood_maps/"

client = boto3.client("s3")
result = client.list_objects(Bucket=bucket, Prefix=_root_dir, Delimiter="/")
members = []
for _sub_prefix in result.get("CommonPrefixes"):
    _prefix = _sub_prefix["Prefix"]
    _prefix_path = Path(_prefix)
    _prefix_result = client.list_objects(Bucket=bucket, Prefix=_prefix, Delimiter="/")
    _event_files = [
        str(Path(_c["Key"]).relative_to(_prefix_path.parent))
        for _c in _prefix_result.get("Contents")
    ]
    members.extend(_event_files)
print(json.dumps(members))
