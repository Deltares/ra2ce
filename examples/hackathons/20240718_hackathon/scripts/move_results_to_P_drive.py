import json
from pathlib import Path

import boto3


"""
WARNING:
You need to refresh yur token in your /users/.aws/credentials file in order to run this script.
"""

# s3://ra2ce-data/
bucket = "ra2ce-data"
_root_dir = "hackathon_july/uq3_results/"
_destination_dir = Path(r'C:\Users\hauth\OneDrive - Stichting Deltares\Documents\tempo\RACE cases\hackathon july')

client = boto3.client("s3")
result = client.list_objects(Bucket=bucket, Prefix=_root_dir, Delimiter="/")

#Iterate through the subdirectories:
for event in result.get("CommonPrefixes"):
    prefix = event.get("Prefix")
    query = client.list_objects(Bucket=bucket, Prefix=prefix, Delimiter="/")
    _res_files = [Path(_c["Key"]).stem for _c in query.get("Contents")]

    # create a subdirectory for each event:
    _event_dir = _destination_dir.joinpath(Path(prefix).name)
    _event_dir.mkdir(parents=True, exist_ok=True)

    # copy files in destination dir:
    for _file in query.get("Contents"):
        _file_name = Path(_file["Key"]).name
        _destination_file = _event_dir.joinpath(_file_name)
        _file_content = client.get_object(Bucket=bucket, Key=_file["Key"])["Body"].read()
        _destination_file.write_bytes(_file_content)

