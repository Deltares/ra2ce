FROM continuumio/miniconda3

SHELL ["/bin/bash","-l", "-c"]

WORKDIR /root/

# Install Miniconda
RUN /opt/conda/bin/conda init bash && \
    /opt/conda/bin/conda config --add channels conda-forge && \
    /opt/conda/bin/conda update conda -y && \
    /opt/conda/bin/conda install -c conda-forge mamba -y && \
    /opt/conda/bin/conda clean -afy

# =================================

# Add conda bin to path
ENV PATH /opt/conda/bin:$PATH

# Copy paths
COPY .config/docker_environment.yml environment.yml

# Create environment
RUN mamba env create -f environment.yml

# Make RUN commands use the new environment:
# SHELL ["conda", "run", "--no-capture-output", "-n", "ra2ce_env", "/bin/bash", "-c"]
# RUN pip install .

# Set up environment
RUN echo "conda activate ra2ce_env" >> ~/.bashrc

# Set entrypoint to bash
ENTRYPOINT ["bash", "-l", "-c"]