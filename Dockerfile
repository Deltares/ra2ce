FROM continuumio/miniconda3
COPY environment.yml .
RUN conda config --set channel_priority strict
RUN conda env create -f environment.yml
ARG conda_env=ra2ce
ENV PATH /opt/conda/envs/$conda_env/bin:$PATH
ENV CONDA_DEFAULT_ENV $conda_env
COPY . app
WORKDIR app
RUN pip install -e .
