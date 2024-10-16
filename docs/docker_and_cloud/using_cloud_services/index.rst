.. _using_cloud_services:

Using cloud services
====================

A variety of different cloud services are available to run ra2ce "on the cloud", both internal and external to Deltares facilities. Here we list the ones we have tested and therefore can provide (certain) support.

Available cloud services:

- Ra2ce S3 (Amazon web services, aws).
  - Allows to run docker containers by using kubernets.
  - Allows to store data to use in the containers.
- Deltares docker harbor.
  - Allows to push and pull ra2ce docker images.

In this subsection you can finde user guidelines on how to use all of them.

.. toctree::
   :caption: Table of Contents
   :maxdepth: 1

   docker_user_guide
   deltares_harbor
   deltares_hpc_user_guide
   hackathon_user_guide