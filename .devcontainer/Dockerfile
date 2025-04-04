# To build this docker run:
# `docker build -t ra2ce_core_dev`
# To run the docker for pytest:
# `docker run -v {your_ra2ce_checkout_dir}:/usr/src/app/ -v {ra2ce_env_dir}:/usr/src/.env -it ra2ce_core_dev`
# `poetry install`
# `poetry run pytest -m {your_pytest_arguments}`
FROM containers.deltares.nl/gfs-dev/ra2ce_externals:latest

RUN apt-get update && apt-get install libgl1 -y && apt-get install --reinstall make

ARG SRC_ROOT="/usr/src"
ARG SRC_EXTERNALS="${SRC_ROOT}/test_external_data"

# For persisting the environment remember to mount it as well:
# -v {your_local_tmp_dir}:/usr/src/.env
ARG CONDA_ENV="${SRC_ROOT}/.env"

# Install conda environment
# This location needs to be mounted with your ra2ce checkout:
# -v {your_ra2ce_checkout_dir}:/usr/src/app
WORKDIR $SRC_ROOT/app
COPY environment.yml $SRC_ROOT/.devcontainer/environment.yml

RUN conda init bash \
    && . ~/.bashrc \
    && conda env create -f $SRC_ROOT/.devcontainer/environment.yml -p $CONDA_ENV

# Activate conda environment
ENV PATH $CONDA_ENV/bin:$PATH
RUN conda activate ${CONDA_ENV} & poetry config virtualenvs.create false
RUN echo conda init && echo "conda activate ${CONDA_ENV}" >>  ~/.bashrc
# This ensures it's available also for `sh` instead of `bash`.
RUN echo "conda activate ${CONDA_ENV}" > ~/.profile

# Define the endpoint
CMD [ "/bin/bash" ]