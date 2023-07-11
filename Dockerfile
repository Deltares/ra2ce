FROM  mambaorg/micromamba:1.4-alpine AS full
ENV HOME=/home/mambauser
WORKDIR ${HOME}
USER mambauser
# RUN apt-get -qq update && apt-get install --yes --no-install-recommends libgdal-dev libgeos-dev libproj-dev && apt-get -qq purge && apt-get -qq clean && rm -rf /var/lib/apt/lists/*
COPY .config/environment.yml pyproject.toml README.rst ${HOME}/
RUN micromamba create -f environment.yml -y --no-pyc \
    && micromamba clean -ayf \
    && rm -rf ${HOME}/.cache \
    && find /opt/conda/ -follow -type f -name '*.a' -delete \
    && find /opt/conda/ -follow -type f -name '*.pyc' -delete \
    && find /opt/conda/ -follow -type f -name '*.js.map' -delete  \
    && rm environment.yml
COPY examples/ ${HOME}/examples
COPY ra2ce/ ${HOME}/ra2ce
RUN micromamba run pip install --no-cache-dir notebook jupyterlab \
    && micromamba run -n ra2ce_env pip install . --no-cache-dir --no-compile --disable-pip-version-check --no-deps\
    && micromamba clean -ayf \
    && find /opt/conda/ -follow -type f -name '*.a' -delete \
    && find /opt/conda/ -follow -type f -name '*.pyc' -delete \
    && find /opt/conda/ -follow -type f -name '*.js.map' -delete
ENTRYPOINT [ "micromamba", "run", "-n", "ra2ce_env" ]
