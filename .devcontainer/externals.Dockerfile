# To build this docker (from the root checkout) run:
# `podman build -t ra2ce_externals -f .devcontainer/externals.Dockerfile`
# do not forget to locate the externals directory on the root folder, 
# otherwise it won't copy anything into the docker image.

# We use a light weight ubuntu image as we only intend to store data through it.
FROM alpine:latest

ARG SRC_ROOT="/usr/src"

# Install conda environment
WORKDIR $SRC_ROOT/app
COPY externals $SRC_ROOT/test_external_data

# Define the endpoint
CMD [ "/bin/bash" ]