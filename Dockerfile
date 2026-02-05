# To build this docker image run:
# `podman build -t ra2ce`

FROM python:3.11

RUN apt-get update && apt-get install -y libgdal-dev

# Copy the directories with the local ra2ce.
WORKDIR /app
COPY README.md LICENSE pyproject.toml /app/
COPY ra2ce /app/ra2ce

# Install ra2ce and its dependencies.
RUN pip install --upgrade pip && pip install /app

# Set the entrypoint to run ra2ce as a module.
ENTRYPOINT [ "python", "-m", "ra2ce" ]