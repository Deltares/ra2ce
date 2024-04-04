#!/bin/bash
 
#SBATCH --exclusive
#SBATCH --job-name=ra2ce-run
#SBATCH --output=log/ra2ce-run_%j.log    # Standard output and error log
#SBATCH --partition=1vcpu
 
echo "STARTING $(date)"
docker run --mount src=${PWD},target=/data,type=bind containers.deltares.nl/ra2ce/ra2ce:latest python /data/run_race.py
wait
echo "ENDED $(date)"
 
wait
# All is good
exit 0