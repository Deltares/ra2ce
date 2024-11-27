# To build this docker run:
# `docker build -t ra2ce`

FROM python:3.11

RUN apt-get update && apt-get install -y libgdal-dev

# Copy the directories with the local ra2ce.
WORKDIR /ra2ce_src
COPY README.md LICENSE pyproject.toml poetry.lock /ra2ce_src/
COPY ra2ce /ra2ce_src/ra2ce

# Install the required packages
RUN pip install poetry
RUN poetry config virtualenvs.create false
# RUN poetry install --without dev,docs,jupyter
RUN poetry install
RUN apt-get clean autoclean

# Define the endpoint
CMD ["python3"]