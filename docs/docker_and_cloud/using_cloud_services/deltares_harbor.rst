.. _deltares_harbor:

Deltares Docker Harbor
======================

Deltares provides us with the possibility to publish our docker images to an internal repository, which enables the possibility of remotely storing our images and running them in different cloud systems.

This repository is located in `https://containers.deltares.nl/ra2ce/ <https://containers.deltares.nl>`_, and the images get automatically pushed from teamcity when all the tests run correctly following the same format:

- (Merge) commits to ``master`` produce a new image ``ra2ce:latest``.
- Pushed tags (format ``v.MAJOR.Minor.patch``) produce a new image ``ra2ce:v_MAJOR_Minor_patch``. 
- Hackathon branches (``hackathon/branch_name``) produce a new image ``ra2ce_hackathon_branch_name:latest``.

They can subsequently be retrieved as ``containers.deltares.nl/ra2ce/ra2ce:desired_tag``

In addition, other branches can also be manually triggered from TeamCity. These images can be retrieved as ``containers.deltares.nl/ra2ce/ra2ce_name_of_the_branch:latest``

.. _deltares_harbor_access_rights:

Access permissions
------------------

In principle anyone should have ``pull`` rights (allows to download the docker images), if ``push`` rights are required please contact our project administrator (`Carles Soriano Pérez <carles.sorianoperez@deltares.nl>`_) or any of the ra2ce team members if not reachable. 

Once ``push`` permissions are granted your local docker machine needs to know of its location, you can do so by simply running the following command:

.. code-block:: bash

    docker login -u <<deltares_email>> -p <<cli_secret>>

.. note::
    To retrieve your ``cli_secret`` go to `<https://containers.deltares.nl/>`_ then click on your user on the top right side of the window, a menu will emerge, select ``User Profile`` and then copy the ``CLI secret`` with the copy functionality.

To push your image just run your usual ``docker push`` command but do not forget to correctly tag your image with the ra2ce repository ``containers.deltares.nl/ra2ce/name_of_your_mage:desired_tag``.

.. note::
    In order to make sure your custom branch is being picked up, we recommend bumping its version manually, if you have installed the ``conda`` environment you should be able to run the `commitizen <https://commitizen-tools.github.io/commitizen/>`_ bump line ``cz bump --devrelease your_custom_release_number``.