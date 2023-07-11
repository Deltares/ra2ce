FROM continuumio/miniconda3
RUN apt-get -qq update && apt-get install --yes --no-install-recommends libgdal-dev libgeos-dev libproj-dev && apt-get -qq purge && apt-get -qq clean && rm -rf /var/lib/apt/lists/*
COPY . .
RUN conda env create -f .config/environment.yml -p .ra2ce_env && conda activate .ra2ce_env && poetry install