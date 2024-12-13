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

- Have docker desktop installed and the application open (check introduction of :ref:`docker_user_guide_installation`). 
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
- Have rights to publish on the registry (check :ref:`deltares_harbor_access_rights`).
 
We (re)build the image with the correct registry prefix.

    .. code-block:: bash

        cd ra2ce 
        Docker build -t containers.deltares.nl/ra2ce/ra2ce:matthias_test .
    
    .. note::
        registry_name/project_name/container_name:tag_name
 

You can check again whether the image is correctly built with any of the following commands: 

    .. code-block:: bash

        docker run -it containers.deltares.nl/ra2ce/ra2ce:user_test 
        docker run -it containers.deltares.nl/ra2ce/ra2ce:user_test bash 
        docker run -it containers.deltares.nl/ra2ce/ra2ce:user_test python -c "import ra2ce; print(ra2ce.__version__)"


Then push to the online registry: 

    .. code-block:: bash
        
        docker push containers.deltares.nl/ra2ce/ra2ce:user_test 

 
Use argo workflows
----------------------

**Prerequisites**:  

- Have kubectl installed (:ref:`docker_user_guide_installation`)
- Have argo installed (:ref:`argo_local_installation`)
- Have aws installed (You can install and configure AWS CLI by following `the official user guidelines <https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html>`_)


1. In ``C:\Users\{you_username}\.aws``, modify ``config``, so that: 

    .. code-block:: ini

        [default] 
        region=eu-west-1 


2. Go to `<https://deltares.awsapps.com/start/#/?tab=accounts>`_ :
    - You will see the ``RA2CE`` aws project, click on it.
    - Select now ``Access keys``, a pop-up will show
    - Copy the content of option 2, the ``Copy`` button will do it for you. It should be something like:

        .. code-block:: ini

            [{a_series_of_numbers}_AWSPowerUserAccess]
            aws_access_key_id={an_access_key_id}
            aws_secret_access_key={a_secret_access_key}
            aws_session_token={a_session_token}


3. Now, go again to ``C:\Users\{you_username}\.aws``, 
    - replace the ``credentials`` content with that of step 2,
    - replace the header so it only containts ``default``,
    - the final content of ``credentials`` should be something as:

        .. code-block:: ini

            [default]
            aws_access_key_id={an_access_key_id}
            aws_secret_access_key={a_secret_access_key}
            aws_session_token={a_session_token}

    .. warning::
        These credentials need to be refreshed EVERY 4 hours! 


4. We will now modify ``C:\Users\{you_username}\.kube\config``

    .. code-block:: bash

        aws eks --region eu-west-1 update-kubeconfig --name ra2ce-cluster 
    
    .. note::
        ``aws eks update-kubeconfig --region {region-code} --name {my-cluster}``
    
    .. warning::
        This step has not been entirely verified as for now we were not able to generate the required data in a 'clean' machine. Instead we copy & pasted the data in a machine where it was already properly configured.

5. Now we forward the kubernetes queue status to our local argo:

    .. code-block:: bash
        
        kubectl -n argo port-forward service/argo-server 2746:2746 

6. It should now be possible to access your local argo in `<https://localhost:2746>`_
    - An authentication token will be required, you can request it via command line:
        
        .. code-block:: bash
            
            argo auth token
    - Copy and paste it.

    .. note::
        This authentication code expires within 15 minutes, you will have to refresh it multiple times.
        If you don't want to do this you can always get the current status with:

            .. code-block:: bash
                
                kubectl get pods -n argo
            
            .. note::
                ``-n argo`` means namespace argo.

7. Submit a workflow
    - Navigate to the location of your ``.yml`` (or ``.yaml``) workflow.
    - Ensure the workflow's namespace is set to ``argo``, the ``.yml`` should start with something like:

        .. code-block:: yaml

            apiVersion: argoproj.io/v1alpha1
            kind: Workflow
            metadata:
                namespace: argo

    - Execute the following command
        
        .. code-block:: bash
            
            kubectl create -f {your_workflow}.yml 
        
    - You can track the submitted workflow as described in steps 5 and 6.