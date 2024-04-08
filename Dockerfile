# 1. To build this docker run:
# `docker build -t ra2ce`

FROM python:3.10

RUN apt-get update && apt-get install -y libgdal-dev

COPY .config/docker_requirements.txt requirements.txt
# The following step happens in the `workflow.yaml`
# COPY hackathon/hazard_overlay_cloud_run.py ./scripts/run_hazard_overlay.py

RUN pip install numpy
RUN pip install GDAL==3.5.1
RUN pip install git+https://github.com/Deltares/ra2ce.git

CMD ["python", "/script/run_race.py"]

# 2. Make sure you push it to the deltares containers
# docker tag ra2ce containers.deltares.nl/ra2ce/ra2ce:latest
# docker push containers.deltares.nl/ra2ce/ra2ce:latest