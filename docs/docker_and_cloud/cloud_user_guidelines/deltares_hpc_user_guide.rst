.. _deltares_hpc_user_guide:

Deltares HPC User Guide
==================

Introduction
---------------------------------
This user guide introduces how to run Ra2ce in a HPC environment.
The HPC environment will need to support Docker containers. Not every
HPC environment will but the Deltares H7 HPC does.

Running Ra2ce Docker container on H7
-------------------------------------

Access the head node of the H7. Detailed instructions can be found on our public Wiki: https://publicwiki.deltares.nl/display/Deltareken/Access

The Wiki is be the place to see the latest information on how to use the H7. So if anything in this
user guide does not work as expected use the Wiki to see if anything changed.

In short, you can access the H7 using SSH or RDP.

.. code-block:: bash

  ssh h7.directory.intra

Move all the input data to a p drive of your project. In the Ra2ce repository there is a
slurm_job.sh file that also needs to be moved to an accessible location (the same p drive for example)

Navigate to the p drive on the head node

.. code-block:: bash

  cd /p/<<project number>>

Now you can schedule the job using slurm. Slurm is a job orchestrator used with many HPC environments.

In the slurm job there are resource requests set up. Adjust your slurm_job.sh file where needed for your use case.

See all options on the Wiki: 

In the slurm job for Ra2ce we just run 1 command.

.. code-block:: bash
    
  docker run --mount src=${PWD},target=/data,type=bind containers.deltares.nl/ra2ce/ra2ce:latest python /data/run_race.py``

+------------------------------------------------+---------------------------------------------------------------+
| Command                                        | Description                                                   |
+------------------------------------------------+---------------------------------------------------------------+
| docker run                                     | The command to run a docker container                         |
| --mount src=,target=,type=bind                 | This mounts the current folder to a target location in the    |
|                                                | Docker container                                              |
| containers.deltares.nl/ra2ce/ra2ce:latest      | The container image and version to run. If you want older     |
|                                                | versions you can change the latest tag                        |
| python /data/run_race.py                       | The command to run in the container                           |
+------------------------------------------------+---------------------------------------------------------------+

Make sure your run_race.py writes to the mounted drive or you will lose your output once the job is finished.

.. code-block:: bash

    sbatch slurm_job.sh

See the progress of your job here: https://hpcjobs.directory.intra/
