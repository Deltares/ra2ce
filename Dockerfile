# Run with `docker build -t ra2ce .`
FROM  mambaorg/micromamba:1.4-alpine AS full

# ENV_NAME is starting a bash inm this environment 

ENV HOME="/home/mambauser"
ENV ENV_NAME=ra2ce_env

ENV PATH="${PATH}:/home/mambauser"

# Setting workspace vbriables

WORKDIR ${HOME}
USER mambauser
# RUN apt-get -qq update && apt-get install --yes --no-install-recommends libgdal-dev libgeos-dev libproj-dev && apt-get -qq purge && apt-get -qq clean && rm -rf /var/lib/apt/lists/*
COPY .config/environment.yml pyproject.toml README.md ${HOME}/
# Creating ra2ce2_env

RUN micromamba create -f environment.yml -y --no-pyc \
    && micromamba clean -ayf \
    && rm -rf ${HOME}/.cache \
    && find /opt/conda/ -follow -type f -name '*.a' -delete \
    && find /opt/conda/ -follow -type f -name '*.pyc' -delete \
    && find /opt/conda/ -follow -type f -name '*.js.map' -delete  \
    && rm environment.yml

# COPY examples/ ${HOME}/examples
COPY ra2ce/ ${HOME}/ra2ce

ENV PYTHONPATH="$/opt/conda/envs/ra2ce_env/bin:${PYTHONPATH}"
ENV PATH="/opt/conda/envs/ra2ce_env/bin:${PATH}"
RUN echo "conda activate ra2ce_env"

SHELL ["/bin/bash","-l", "-c"]

EXPOSE 5000
CMD ["python"]