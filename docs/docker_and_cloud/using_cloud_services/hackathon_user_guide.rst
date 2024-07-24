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
    - Have the ``ra2ce`` repository checked out in your machine (check how to install ``ra2ce`` in :ref:`_install_ra2ce_devmode`).
        - This guideline will be based on a checkout tagged version ``v0.9.2``
    - Run a command line using said check-out as your working directory.

First, lets bump the local ``ra2ce`` version so we can track whether our image has been correctly built later on.

    .. code-block:: bash
        $ cz bump --devrelease 0 --increment patch
        bump: version 0.9.2 → 0.9.3.dev0
        tag to create: v0.9.3
        increment detected: PATCH

.. warning::
    This creates a local tag, which you don't need to push (and it's best not to). If you wish to continue working without incrementing the patch number you can do the following:
    
    - Modify any of the files from the repository.
    - Commit the changes.
    - Execute the above command without the ``--increment patch`` option: ::
        
        $ cz bump --devrelease 0 
        bump: version 0.9.2 → 0.9.2.dev0

We can build a docker image based on the docker file located in the repo

    .. code-block:: bash
        cd ra2ce 
        docker build -t ra2ce:latest . 
        docker images        (this returns a list of all images available.) 
        docker run -it ra2ce:latest /bin/bash       (adapt IMAGE_ID) 

 
The command line looks like: ``(ra2ce_env) 4780e47b2a88:~$ ``, and you can navigate it by using ``cd`` and ``ls`` (it's a Linux container).
``ra2ce`` should be installed in the image and ready to be used as a "package", you can verify its installation by simply running:
    .. code-block:: bash
        $ docker run -it ra2ce:latest python -c "import ra2ce; print(ra2ce.__version__)"
        0.9.2.dev1


Do now ``cd`` to the directory of the python and run: 

python -m workflow_hazard_overlay.py 

Poetry install      (if necessary) 


2. Push a docker image
-----------------------

3. Use argo workflows
----------------------
