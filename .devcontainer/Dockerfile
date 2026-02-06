# To build this docker image run:
# `podman build -t ra2ce_core_dev`
# To run the docker image for pytest:
# `podman run -v {your_ra2ce_checkout_dir}:/usr/src/app/ -v {ra2ce_env_dir}:/usr/src/.env -it ra2ce_core_dev`
# `pixi install`
# `pixi run pytest -m {your_pytest_arguments}`
FROM containers.deltares.nl/gfs-dev/ra2ce_externals:latest AS externals

FROM ghcr.io/prefix-dev/pixi:latest AS base_pixi

RUN apt-get update && apt-get install libgl1 -y && apt-get install --reinstall make

ARG SRC_ROOT="/usr/src"
ARG SRC_EXTERNALS="${SRC_ROOT}/test_external_data"


# Set PIXI_HOME to a location inside the source root
ENV PIXI_HOME=$SRC_ROOT/.pixi

# Copy externals from dockerfile
WORKDIR $SRC_ROOT/app
COPY --from=externals $SRC_EXTERNALS $SRC_EXTERNALS

# Define the endpoint
CMD [ "/bin/bash" ]