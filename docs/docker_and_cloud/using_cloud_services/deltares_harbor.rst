.. _deltares_harbor:

Deltares Docker Harbor
======================

Deltares provides us with the possibility to publish our docker images to an internal repository, which enables the possibility of remotely storing our images and running them in different cloud systems.

This repository is located in `https://containers.deltares.nl/ra2ce`, and the images get automatically pushed from teamcity when all the tests run correctly following the same format:

- (Merge) commits to ``master`` produce a new image ``ra2ce:latest``.
- Pushed tags (format ``v.MAJOR.Minor.patch``) produce a new image ``ra2ce:v_MAJOR_Minor_patch``. 
- Hackathon branches (``hackathon/branch_name``) produce a new image ``ra2ce_hackathon_branch_name:latest``.

In addition, other branches can also be manually triggered from TeamCity.

Access permissions
------------------

In principle anyone should have ``pull`` rights (allows to download the docker images), if ``push`` rights are required please contact our project administrator (`carles.sorianoperez@deltares.nl`) or any of the ra2ce team members if not reachable.