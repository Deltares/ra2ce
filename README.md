[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3111/)
[![GitHub Pages documentation](https://github.com/Deltares/ra2ce/actions/workflows/deploy_docs.yml/badge.svg)](https://github.com/Deltares/ra2ce/actions/workflows/deploy_docs.yml)
[![Binder branch](https://github.com/Deltares/ra2ce/actions/workflows/binder_branch.yml/badge.svg)](https://github.com/Deltares/ra2ce/actions/workflows/binder_branch.yml)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Deltares/ra2ce/jupyter-binder)

# Ra2ce Examples

This directory contains all (current) available examples of `ra2ce`. An environment file (intended for [Binder](#binder-requirements)) is provided with a preinstalled version of our latest changes in `master` (which might differ from our latest public release) and can be installed with cnoda as this:

```
conda env create -f environment.yml
conda activate ra2ce_examples_env
python import ra2ce
```

> [!important]
> This environment file is intended to be used only by the Binder requirement. 
> If you wish to run the examples in a jupyter notebook you might require to install `ipykernel` and `ipython`. 
> You can do this in your IDE's console:
> `conda install ipykernel`
> `conda install ipython`


At the same time you may use our [binder environment](https://mybinder.org/v2/gh/Deltares/ra2ce/jupyter-binder).

Please refer to our [Ra2ce documentation](https://deltares.github.io/ra2ce/) for more information.

## Binder requirements.
Binder requires the `apt.txt` and the `environment.yml` files to be present. Do not remove them from this repository.

### Installing a different ra2ce version

If you wish to run a different `ra2ce` version you will have to manually do so:

1. Remove the current `ra2ce` version:

`pip remove ra2ce`

2. Install your desired version (for instance an unpublished to pypi):

`pip install git+https://github.com/Deltares/ra2ce.git@an_unpublished_tag`

3. Or you can also install the latest available published one (rather than the one from GitHub):

`pip install ra2ce`

## Configuration
Examples that focus on the analysis stage have the network predefined in `static\output_graph` to ensure a stable network.