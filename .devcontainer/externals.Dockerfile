# To build this docker (from the root checkout) run:
# `docker build -t vrtool_externals -f .devcontainer/externals.Dockerfile`

# We use a miniforge3 image for consistency with the other development image.
FROM ghcr.io/prefix-dev/pixi:latest

ARG SRC_ROOT="/usr/src"

# Install conda environment
WORKDIR $SRC_ROOT/app
COPY externals $SRC_ROOT/test_external_data

# Define the endpoint
CMD [ "/bin/bash" ]