# 1. To build this docker run:
# `docker build -t ra2ce`

FROM python:3.10

RUN apt-get update && apt-get install -y libgdal-dev

# The following step happens in the `workflow.yaml`
# COPY hackathon/hazard_overlay_cloud_run.py ./scripts/run_hazard_overlay.py
RUN pip install --no-cache-dir boto3
RUN pip install ra2ce
CMD ["python"]

# 2. Make sure you push it to the deltares containers
# docker tag ra2ce containers.deltares.nl/ra2ce/ra2ce:latest
# docker push containers.deltares.nl/ra2ce/ra2ce:latest