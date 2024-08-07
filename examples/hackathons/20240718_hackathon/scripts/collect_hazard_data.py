import json
from pathlib import Path

import boto3

# s3://ra2ce-data/
bucket = "ra2ce-data"
_root_dir = "hackathon_july/hazard_files/"

client = boto3.client("s3")
result = client.list_objects(Bucket=bucket, Prefix=_root_dir, Delimiter="/")
_event_files = [Path(_c["Key"]).stem for _c in result.get("Contents")]

# Dump the name of the `.tif` files WITHOUT the extension.
print(json.dumps(_event_files))
