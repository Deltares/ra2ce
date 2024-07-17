# 1. To build this docker run:
# `docker build -t ra2ce`
FROM python:3.10


RUN apt-get update && apt-get install -y libgdal-dev

# Copy the directories with the local ra2ce.
COPY ra2ce/ ra2ce/
COPY README.md README.md
COPY LICENSE LICENSE
COPY pyproject.toml pyproject.toml

# Install the required packages
RUN pip install poetry
RUN poetry install
RUN pip install --no-cache-dir boto3

CMD ["python"]

# 2. Make sure you push it to the deltares containers
# docker tag ra2ce containers.deltares.nl/ra2ce/ra2ce:latest
# docker push containers.deltares.nl/ra2ce/ra2ce:latest