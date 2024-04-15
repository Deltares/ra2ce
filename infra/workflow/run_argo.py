## This script can be used as a template to create Argo workflows using Python code (instead of a YAML file)

import os

from hera import Task, Workflow, WorkflowService, WorkflowStatus
from hera.global_config import GlobalConfig

GlobalConfig.host = ""
GlobalConfig.verify_ssl = False
GlobalConfig.token = ""
GlobalConfig.namespace = "argo"


class Argo:
    def __init__(self, name):
        pass

    def submit_single_job(model):
        with Workflow(
            model.name.replace("_", "-"),
            generate_name=True,
            workflow_template_ref="race-workflow",
        ) as w:
            Task(
                "ra2ce-argo",
                image="containers.deltares.nl/ra2ce/ra2ce:latest",
                command=["/bin/bash", "-c", "--"],
                args=["python", "/scripts/run_race.py"],
            )

        return w.create()

    def get_task_status(workflow):
        status = workflow.get_status()

        if status == WorkflowStatus.Succeeded:
            return True

        return False
