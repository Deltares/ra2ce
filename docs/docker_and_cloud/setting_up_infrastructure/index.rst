.. _setting_up_infrastructure:

Setting up infrastructure 
=========================

At the moment, the ``ra2ce`` "cloud" infrastructure consists of three main components:

- Amazon web services `s3 <https://deltares.awsapps.com/>`_.
   - Stores data.
   - Runs docker components through Kubernetes
- Kubernetes.
   - Creates and runs the ``ra2ce`` docker images in containers.
   - Runs custom scripts in the related containers.
- Argo.
   - "Orchastrates" how a workflow will be run in the s3 using kubernetes.
   - Workflows ar ``*.yml`` files describing the node types and resources to use at each step of a cloud run.


.. toctree::
   :caption: Table of Contents
   :maxdepth: 1

   kubernetes_deployment
   argo_deployment