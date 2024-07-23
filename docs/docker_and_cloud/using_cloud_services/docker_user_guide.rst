.. _docker_user_guide:

Docker User Guide
==================

Introduction
---------------------------------
This user guide introduces how to run Ra2ce in a public cloud environment.


How to build the cloud docker image
-----------------------------------

Assuming access to a Linux box with Docker installed, or in Windows a Docker Desktop installation. You can do the 
following:

   .. code-block:: bash

      git clone git@github.com:Deltares/ra2ce.git
      cd ra2ce
      docker build -t ra2ce:latest -f Dockerfile .

These instructions will build a docker image. After a good while, you should end up with:

   .. code-block:: bash

      $ docker images
      REPOSITORY   TAG       IMAGE ID       CREATED        SIZE
      ra2ce         latest    616f672677f2   19 hours ago   1.01GB

Remark that this is a local image only.


Running Ra2ce Docker container locally
--------------------------------------

To run the Docker container locally you can execute the following command:

.. code-block:: bash
   
   docker run -it ra2ce bash

This will create a Docker container from the specified image and start an interactive shell in which you can enter commands

In this cloud version of the Docker container there is no Jupyter notebook available to interact with the Ra2ce package.
Instead you can start Ra2ce from the command line or write an input script (Python) similar to a Jupyter notebook.

If you wish to include files (i.e. input files and run files) you can mount folders to your Docker container on run with for example:

.. code-block:: bash
   
   docker run -it -v $PWD/workflow:/scripts -v $PWD/tests/test_data/acceptance_test_data/:/data ra2ce_package bash

After that you can call run_race.py. Output files will be available in the acceptance_test_data folder

Running Ra2ce container in a cloud environment
----------------------------------------------

In the local example you are running a Docker container entirely locally and thus can mount your own hard drive with input data.

In a cloud environment this is not possible so we have additional requirements:

- A compute environment that is responsible to run a Docker container on a remote server.
- A data storage environment that can be mounted to the container mimicking the way we run a container locally
- A workflow orchestrator that can manage mounting the afformentioned data storage layer and manage a workflow of multiple container instances.

Currently we have tested Ra2ce using the following tech stack:

- Kubernetes (AWS EKS) as compute environment. If there is no environment currently available check the ``/infra/README.md`` on how to set it up.
- AWS S3 as data storage layer.
- Argo Workflow as workflow orchestrator. If there is no Argo deployment currently available see ``/infra/workflow/README.md`` on how to deploy Argo.

Running a singular Ra2ce container in Kubernetes
-------------------------------------------------

In Kubernetes, you can deploy Docker containers stored in container registries such as Docker Hub or any other container registry provider. This guide illustrates how to run a Docker container from an existing container registry using ``kubectl``.

Prerequisites
-------------

Before following this guide, ensure you have the following:

- A Kubernetes cluster set up.
- ``kubectl`` installed and configured to connect to your Kubernetes cluster.
- Docker container image pushed to a container registry accessible to your Kubernetes cluster.

Steps
-----

1. **List Available Images**: First, list the available Docker container images in your container registry. You will need the full image name for the subsequent steps.

2. **Create Deployment YAML**: Create a YAML file specifying the details of the container you want to run. An example YAML file is available in ``/infra/workflow/pod.yaml``:

   Replace ``<your-image-name>:<tag>`` with the full image name and tag of your Docker container image, and ``<port>`` with the port your container listens on.

3. **Apply Deployment**: Apply the deployment YAML using ``kubectl``:

   .. code-block:: bash

      kubectl apply -f pod.yaml

   Replace ``pod.yaml`` with the filename of your deployment YAML file.

4. **Verify Deployment**: Check if the deployment was successful:

   .. code-block:: bash

      kubectl get pods

   You should see your deployment listed with 1 desired replica and 1 current replica.

5. **Access the Running Container**: You can access the logs of the running container or execute commands within the container using ``kubectl``. For example:

   - To view container logs:

     .. code-block:: bash

        kubectl logs <pod-name>

     Replace ``<pod-name>`` with the name of your pod.

   - To execute a command in the container:

     .. code-block:: bash

        kubectl exec -it <pod-name> -- <command>

     Replace ``<command>`` with the command you want to execute in the container.

Running a Ra2ce workflow in Argo
---------------------------------

Introduction
------------

Argo Workflows is an open-source workflow engine optimized for Kubernetes. This guide demonstrates how to run a simple Argo workflow on your Kubernetes cluster.

Prerequisites
-------------

Before following this guide, ensure you have the following:

- A Kubernetes cluster set up.
- ``kubectl`` installed and configured to connect to your Kubernetes cluster.
- Argo Workflows installed in your Kubernetes cluster. You can install Argo Workflows by following the official documentation: `<https://argoproj.github.io/argo-workflows/>`_

Steps
-----

1. **Create Workflow YAML**: Create a workflow YAML file specifying the steps of your workflow. An example YAML file is available in ``/infra/workflow/pod.yaml``:

   Replace ``<your-image-name>:<tag>`` with the Docker container image you want to use in your workflow.

2. **Submit Workflow**: Submit the workflow YAML using ``kubectl``:

   .. code-block:: bash

      kubectl apply -f workflow.yaml

   Replace ``workflow.yaml`` with the filename of your workflow YAML file.

3. **Check Workflow Status**: Monitor the status of your workflow using Argo CLI or Argo UI. To use Argo CLI:

   - Install Argo CLI by following the official documentation: `<https://argoproj.github.io/argo-workflows/cli/>`_
   - Check the status of your workflow:

     .. code-block:: bash

        argo list

     This command lists all workflows, including the one you just submitted.

   - To view detailed information about your workflow:

     .. code-block:: bash

        argo get <workflow-name>

     Replace ``<workflow-name>`` with the name of your workflow.