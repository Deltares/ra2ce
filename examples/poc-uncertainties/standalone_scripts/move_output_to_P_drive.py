import json
from pathlib import Path

import boto3


"""
WARNING:
You need to refresh yur token in your /users/.aws/credentials file in order to run this script.
"""

# s3://ra2ce-data/
bucket = "ra2ce-data"
_root_dir = "hackathon_uncertainty/output_2/"
_destination_dir = Path(r'C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\projects\RACE\RA2CE Proba 2024\output_monte_carlo\output_13_08_test')

client = boto3.client("s3")
result = client.list_objects(Bucket=bucket, Prefix=_root_dir, Delimiter="/")

#Iterate through the subdirectories:
for event in result.get("CommonPrefixes"):
    prefix = event.get("Prefix")
    event_name = Path(prefix).name     # extract the event name:
    query_event = client.list_objects(Bucket=bucket, Prefix=prefix, Delimiter="/")

    scenarios = [scenario["Prefix"] for scenario in query_event.get("CommonPrefixes")]

    for scenario in scenarios:
        scenario_name = Path(scenario).name
        query_scenario = client.list_objects(Bucket=bucket, Prefix=scenario + "output_graph/", Delimiter="/")
        runs = [run["Prefix"] for run in query_scenario.get("CommonPrefixes")]

        for run in runs:
            query_run = client.list_objects(Bucket=bucket, Prefix=run, Delimiter="/")
            run_name = Path(run).name
            _res_files = [Path(_c["Key"]).stem for _c in query_run.get("Contents")]

            # create a subdirectory for each event:
            _event_dir = _destination_dir.joinpath(event_name, scenario_name, run_name)
            _event_dir.mkdir(parents=True, exist_ok=True)

            # copy files in destination dir:
            for _file in query_run.get("Contents"):
                _file_name = Path(_file["Key"]).name
                _destination_file = _event_dir.joinpath(_file_name)
                _file_content = client.get_object(Bucket=bucket, Key=_file["Key"])["Body"].read()
                _destination_file.write_bytes(_file_content)
