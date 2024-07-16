# Run with `docker build -t ra2ce .`
FROM  mambaorg/micromamba:1.4-alpine AS full

# ENV_NAME is starting a bash inm this environment 

ENV HOME=/home/mambauser
ENV ENV_NAME=ra2ce_env
ENV PYTHONPATH="/home/mambauser:$PYTHONPATH"

# Setting workspace vbriables

WORKDIR ${HOME}
USER mambauser
# RUN apt-get -qq update && apt-get install --yes --no-install-recommends libgdal-dev libgeos-dev libproj-dev && apt-get -qq purge && apt-get -qq clean && rm -rf /var/lib/apt/lists/*
COPY .config/docker_environment.yml pyproject.toml README.md ${HOME}/
RUN mkdir -p ${HOME}/.jupyter
COPY .config/jupyter/* ${HOME}/.jupyter

# Creating ra2ce2_env

RUN micromamba create -f docker_environment.yml -y --no-pyc \
    && micromamba clean -ayf \
    && rm -rf ${HOME}/.cache \
    && find /opt/conda/ -follow -type f -name '*.a' -delete \
    && find /opt/conda/ -follow -type f -name '*.pyc' -delete \
    && find /opt/conda/ -follow -type f -name '*.js.map' -delete  \
    && rm docker_environment.yml
COPY examples/ ${HOME}/examples
COPY ra2ce/ ${HOME}/ra2ce

# Installing notabook and Jupyter  lab
# this is now in the docker_environment.yml

# Expose the Jupyter port
EXPOSE 8080

# Start Jupyter Notebook
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8080", "--allow-root"]