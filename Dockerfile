FROM  mambaorg/micromamba:1.4-alpine AS full

# ENV_NAME is starting a bash inm this environment 

ENV HOME=/home/mambauser
ENV ENV_NAME=ra2ce_env
ENV JUPYTER_PORT=8080

# Setting workspace vbariables

WORKDIR ${HOME}
USER mambauser
# RUN apt-get -qq update && apt-get install --yes --no-install-recommends libgdal-dev libgeos-dev libproj-dev && apt-get -qq purge && apt-get -qq clean && rm -rf /var/lib/apt/lists/*
COPY .config/docker_environment.yml pyproject.toml README.md ${HOME}/

# Creating ra2ce2_env

RUN micromamba create -f docker_environment.yml -y --no-pyc 
#    && micromamba clean -ayf \
#    && rm -rf ${HOME}/.cache \
#    && find /opt/conda/ -follow -type f -name '*.a' -delete \
#    && find /opt/conda/ -follow -type f -name '*.pyc' -delete \
#    && find /opt/conda/ -follow -type f -name '*.js.map' -delete  \
#    && rm docker_environment.yml
COPY examples/ ${HOME}/examples
COPY ra2ce/ ${HOME}/ra2ce

# Installing notabook and Jupyter  lab

#RUN micromamba config append channels conda-forge 
#RUN pip install notebook jupyter

#RUN micromamba run -n ra2ce_env pip install --no-cache-dir notebook jupyterlab 
#    && micromamba run -n ra2ce_env pip install . --no-cache-dir --no-compile --disable-pip-version-check --no-deps\
#    && micromamba clean -ayf \
#    && find /opt/conda/ -follow -type f -name '*.a' -delete \
#    && find /opt/conda/ -follow -type f -name '*.pyc' -delete \
#    && find /opt/conda/ -follow -type f -name '*.js.map' -delete

ENTRYPOINT [ "/bin/bash" ]
#ENTRYPOINT [ "/opt/conda/envs/ra2ce_env/bin/jupyter-lab" ]
