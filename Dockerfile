FROM continuumio/miniconda3
RUN conda env create -f .config/environment.yml -p .env
ARG conda_env=.env
ENV PATH /opt/conda/envs/$conda_env:$PATH
ENV CONDA_DEFAULT_ENV $conda_env
RUN apt-get -qq update && apt-get install --yes --no-install-recommends libgdal-dev libgeos-dev libproj-dev && apt-get -qq purge && apt-get -qq clean && rm -rf /var/lib/apt/lists/*
RUN poetry install
