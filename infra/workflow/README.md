## Submit a Ra2ce workflow (CLI)

argo submit -n argo --watch ./workflow.yaml

The --watch flag used above will allow you to observe the workflow as it runs and the status of whether it succeeds. When the workflow completes, the watch on the workflow will stop.

You can list all the Workflows you have submitted by running the command below:

argo list -n argo

You will notice the Workflow name has a hello-world- prefix followed by random characters. These characters are used to give Workflows unique names to help identify specific runs of a Workflow. If you submitted this Workflow again, the next Workflow run would have a different name.

Using the argo get command, you can always review details of a Workflow run. The output for the command below will be the same as the information shown as when you submitted the Workflow:

argo get -n argo @latest

The @latest argument to the CLI is a short cut to view the latest Workflow run that was executed.

You can also observe the logs of the Workflow run by running the following:

argo logs -n argo @latest

## Submit a Ra2ce workflow (GUI)

Open a port-forward so you can access the UI:

kubectl -n argo port-forward deployment/argo-server 2746:2746

Navigate your browser to https://localhost:2746.

Click + Submit New Workflow and then Edit using full workflow options

You can find an example workflow already in the text field. Press + Create to start the workflow.

## Subit a Ra2ce workflow (Hera)

Hera is an Argo Python SDK. Hera aims to make construction and submission of various Argo Project resources easy.

If you were able to run the argo submit command above, copy the following Workflow definition into a local file hello_world.py.

from hera.workflows import Steps, Workflow, WorkflowsService, script

@script()
def echo(message: str):
    print(message)


with Workflow(
    generate_name="hello-world-",
    entrypoint="steps",
    namespace="argo",
    workflows_service=WorkflowsService(host="https://localhost:2746")
) as w:
    with Steps(name="steps"):
        echo(arguments={"message": "Hello world!"})

w.create()

Run the file

python -m hello_world

You will then see the Workflow at https://localhost:2746/