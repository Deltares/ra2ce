Deploying Argo Workflows with Helm on Amazon EKS
================================================

This guide explains how to deploy Argo Workflows on an Amazon EKS cluster. Argo Workflows is an open-source container-native workflow engine for orchestrating parallel jobs on Kubernetes.

Prerequisites
-------------

Before deploying Argo Workflows, ensure you have the following prerequisites:

- An Amazon EKS cluster. Refer to the kubernetes_deployment.rst in the project directory for instructions on deploying an EKS cluster with Terraform.
- `kubectl` configured to interact with the deployed EKS cluster.

Deployment Steps
----------------

Follow these steps to deploy Argo Workflows on the Amazon EKS cluster:

1. **Create Argo namespace:**

   Create a namespace for Argo to run in:

   ::
    
      kubectl create namespace argo

2. **Install Argo Workflows:**

   Update Helm repositories to ensure you have the latest information:

   ::

      kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/download/v3.5.5/install.yaml

3. **Access Argo UI:**

   Once the installation is complete, you can access the Argo UI by port-forwarding to the Argo server service:

   ::

      kubectl -n argo port-forward service/argo-server 2746:2746

   Open your web browser and navigate to `http://localhost:2746` to access the Argo UI.

Clean Up
--------

To uninstall Argo Workflows from the EKS cluster:

1. **Uninstall Argo Workflows:**

   ::

      kubectl delete deployment argo -n argo

   This command removes the Argo Workflows deployment from the cluster.

