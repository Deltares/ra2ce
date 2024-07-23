.. _kubernetes_deployement:

Deploying Kubernetes on Amazon EKS Cluster with Terraform
=========================================================

This guide outlines the steps to deploy an Amazon EKS cluster using Terraform. The Terraform configuration provided here automates the setup process, making it easier to create and manage an EKS cluster on AWS.

Prerequisites
-------------

Before deploying the EKS cluster, ensure you have the following prerequisites:

- An AWS account with appropriate permissions to create resources like VPCs, subnets, EKS clusters, and EC2 instances.
- Terraform installed on your local machine. You can download it from `terraform official website <https://www.terraform.io/downloads.html>`_ and follow the installation instructions.
- AWS CLI configured with appropriate credentials. You can install and configure AWS CLI by following `the official user guidelines <https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html>`_.

Deployment Steps
----------------

Follow these steps to deploy the Amazon EKS cluster:

1. **Clone the Repository:**

   .. code-block:: bash

      git clone <repository-url>

2. **Navigate to the Project Directory:**

   .. code-block:: bash

      cd <repository-directory>

3. **Update Terraform Backend Configuration:**

   Edit the ``backend.tf`` file and replace ``your-bucket-name`` with your S3 bucket name. Ensure that the bucket is already created, and a DynamoDB table is set up for state locking.

4. **Modify Terraform Configuration:**

   Update the ``main.tf`` file with your desired configurations:

   - Replace ``region`` with your preferred AWS region.
   - Modify ``cluster_name`` with your desired EKS cluster name.
   - Update ``subnets`` with the IDs of your desired subnets.
   - Adjust ``instance_type`` and ``key_name`` in the ``node_groups`` section with your preferred EC2 instance type and key pair name.

5. **Initialize Terraform:**

   .. code-block:: bash

      terraform init

6. **Deploy the EKS Cluster:**

   .. code-block:: bash

      terraform apply

7. **Accessing the Cluster:**

   After the deployment completes, you will get the following outputs:

   - ``cluster_endpoint``: The endpoint URL of the EKS cluster.
   - ``kubeconfig``: The generated kubeconfig file to authenticate with the EKS cluster using ``kubectl``.
   - ``config_map_aws_auth``: The ConfigMap YAML used to configure AWS authentication for the EKS cluster.

   Use the provided kubeconfig file and ``kubectl`` to interact with the deployed EKS cluster:

   .. code-block:: bash

      export KUBECONFIG=$(pwd)/kubeconfig_<your-cluster-name>

      aws eks --region eu-west-1 update-kubeconfig --name ra2ce_cluster

      kubectl get svc

Clean Up
--------

To avoid incurring unnecessary costs, remember to clean up the resources once you're done using the EKS cluster:

1. **Destroy Resources:**

   .. code-block:: bash

      terraform destroy

2. **Manual Clean Up:**

   Ensure all resources associated with the EKS cluster are deleted from the AWS Management Console, including EKS cluster, EC2 instances, security groups, etc.

Further Customization
----------------------

You can either configure the terraform template to add other node groups or follow this documentation to use EKSCTL:

Nodegroups
----------

The nodegroups that are currently available within AWS EKS are:

+-----------+------------------+---------+---------+------------------+--------------+------+------------+
| CLUSTER       | NODEGROUP NAME   | MIN SIZE| MAX SIZE| DESIRED CAPACITY| INSTANCE TYPE| vCPU | MEMORY  |
+===========+==================+=========+=========+==================+==============+======+============+
| ra2ce-cluster | argo-main        | 1       | 25      | 1                | t3-small     |      |        |
+-----------+------------------+---------+---------+------------------+--------------+------+------------+

Adjusting the nodegroups
-------------------------

The size of the nodegroup is adjustable by using eksctl (`<https://eksctl.io/>`_). Eksctl does not work well with AWS SSO unfortunately. You will need to configure your credentials manually.

To increase the current number of nodes (and “overwrite” the Kubernetes behavior):

.. code-block:: bash

   eksctl scale nodegroup --cluster=ra2ce-cluster --nodes=1 --region=eu-west-1 argo-main

This can be done before running a big job where you know you will need a certain number of nodes. This way the Argo workflow does not wait before the needed nodes are available. Kubernetes will still remove nodes if they are not used in a certain time window.

To increase/decrease the minimum number of nodes of a nodegroup:

.. code-block:: bash

   eksctl scale nodegroup --cluster=ra2ce-cluster --nodes-min=0 --region=eu-west-1 argo-main

To increase/decrease the maximum number of nodes of a nodegroup:


.. code-block:: bash

   eksctl scale nodegroup --cluster=ra2ce-cluster --nodes-max=25 --region=eu-west-1 argo-main

Adding Node Groups
-------------------

To add a new node group to your existing EKS cluster, you can use the following command:

.. code-block:: bash

   eksctl create nodegroup --cluster=ra2ce-cluster --region=eu-west-1 --name=newNodeGroup --node-type=t3.medium --nodes=3 --nodes-min=1 --nodes-max=5

This command creates a new node group named "newNodeGroup" with instance type t3.medium and initial 3 nodes. You can adjust the `--nodes-min` and `--nodes-max` parameters as needed.
