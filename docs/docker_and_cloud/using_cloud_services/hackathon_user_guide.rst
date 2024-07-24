.. _hackathon_user_guide:

Hackathon User Guide
====================

This chapter explores the setting up of your local machine to run ``ra2ce`` in a typical "hackathon" case.
Our hackathons usually consist of workflows as:

- Data collection.
- Overlaying hazard(s) based on the data collection.
- Running ``ra2ce`` analysis based on the "n" overlayed hazard network(s).
- Collecting results (post-processing).

Some examples can be found in the :ref:`hackathon_sessions` documentation.

Based on the personal notes of `Matthias Hauth <matthias.hauth@deltares.nl>`_ we will present here how to:

- Build and run a docker image locally,
- Push said image to the Deltares Harbor (:ref:`deltares_harbor`).
- Use argo (:ref:`argo_deployment`) to run workflows in the s3 (:ref:`kubernetes_deployment`).

Keep in mind this documentation could contain information already present in the :ref:`setting_up_infrastructure` subsection.

Build and run a docker image
---------------------------------

**Prerequisites**: 

    - Have docker desktop installed and the application open (check introduction of :ref:`docker_user_guide`). 
    - Have the ``ra2ce`` repository checked out in your machine (check how to install ``ra2ce`` in :ref:`install_ra2ce_devmode`).
    - Run a command line using said check-out as your working directory.

First, lets bump the local ``ra2ce`` version (assume we work based on a ``v0.9.2`` ``ra2ce`` checkout) so we can track whether our image has been correctly built later on.

    .. code-block:: bash
        
        $ cz bump --devrelease 0 --increment patch
        bump: version 0.9.2 → 0.9.3.dev0
        tag to create: v0.9.3
        increment detected: PATCH

.. warning::
    This creates a local tag, which you don't need to push (and it's best not to).
    

We can build a docker image based on the docker file located in the repo

    .. code-block:: bash

        cd ra2ce 
        docker build -t ra2ce:latest . 
        docker images        (this returns a list of all images available.) 
        docker run -it ra2ce:latest /bin/bash       (adapt IMAGE_ID) 

 
The command line looks like: ``(ra2ce_env) 4780e47b2a88:/ra2ce_src~$``, and you can navigate it by using ``cd`` and ``ls`` (it's a Linux container).
``ra2ce`` should be installed in the image and ready to be used as a "package", you can verify its installation by simply running:
    
    .. code-block:: bash
    
        $ docker run -it ra2ce:latest python -c "import ra2ce; print(ra2ce.__version__)"
        0.9.3.dev1


Push a docker image
-----------------------

**Prerequisites**: 
    - Have rights to publish on the registry (check :ref:`_deltares_harbor_access_rights`).
 
 We (re)build the image with the correct registry prefix.

    .. code-block:: bash

        cd ra2ce 
        Docker build -t containers.deltares.nl/ra2ce/ra2ce:matthias_test .
    
    .. note::
        (containers.deltares.nl/ra2ce/ra2ce:matthias_test) 
        (registry_name/project_name/container_name:tag_name) 
 

You can check again whether the image is correctly built with any of the following commands: 

    .. code-block:: bash

        docker run -it containers.deltares.nl/ra2ce/ra2ce:user_test 
        docker run -it containers.deltares.nl/ra2ce/ra2ce:user_test bash 
        docker run -it containers.deltares.nl/ra2ce/ra2ce:user_test python -c "import ra2ce; print(ra2ce.__version__)"


Then push to the online registry: 

    .. code-block::
        
        docker push containers.deltares.nl/ra2ce/ra2ce:user_test 

 


Use argo workflows
----------------------
