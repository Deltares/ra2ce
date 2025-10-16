[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3109/)
[![GitHub Pages documentation](https://github.com/Deltares/ra2ce/actions/workflows/deploy_docs.yml/badge.svg)](https://github.com/Deltares/ra2ce/actions/workflows/deploy_docs.yml)
[![Binder branch](https://github.com/Deltares/ra2ce/actions/workflows/binder_branch.yml/badge.svg)](https://github.com/Deltares/ra2ce/actions/workflows/binder_branch.yml)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Deltares/ra2ce/jupyter-binder)

# Ra2ce Examples

This directory contains all (current) available examples of ra2ce. An environment is ready to run them:
```
conda env create -f environment.yml
conda activate ra2ce_examples_env
python import ra2ce
```

At the same time you may use our [binder environment](https://mybinder.org/v2/gh/Deltares/ra2ce/jupyter-binder).

Please refer to our [Ra2ce documentation](https://deltares.github.io/ra2ce/) for more information.

## Binder requirements.
Binder requires the `apt.txt` and the `environment.yml` files to be present. Do not remove them from this repository.

## Configuration
Examples that focus on the analysis stage have the network predefined in `static\output_graph` to ensure a stable network.