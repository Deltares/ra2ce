.. _installation:

Installation
============

RA2CE can be operated via the command-line interface with two commands. 
Before RA2CE can be used, the correct Python environment needs to be installed 
(see *environment.yml*), this can be done with a conda environment manager such
as `miniforge <https://github.com/conda-forge/miniforge>`_ or `micromamba <https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html>`_.

.. note::
  Important! In compliance with Deltares open-source policy it is recommended to use either ``miniforge`` or ``micromamba``
  as they both have ``conda-forge`` as the default package channel. If you wish to use another conda distribution please 
  make sure the default channel is set to ``conda-forge`` to avoid issues with Deltares open-source policy.


Python package mode
+++++++++++++++++++
In order to use the tool via Python script, install first the RA2CE in your Python environment. RA2CE is available on `PyPI <https://pypi.org/project/ra2ce/>`_ and can be installed using `pip`:

  .. code-block:: bash

    pip install ra2ce
  
Alternatively you can install the latest version available on GitHub or a specific tag / commit hash by using the symbol `@`:

  .. code-block:: bash

    pip install git+https://github.com/Deltares/ra2ce.git
    pip install git+https://github.com/Deltares/ra2ce.git@v0.3.1

Development mode
++++++++++++++++

If you wish to contribute to the development of the tool, please refer for installation to our `installation for contributors wiki page <https://github.com/Deltares/ra2ce/wiki/getting-started#installation-for-contributors>`_.


Docker and cloud
+++++++++++++++++++++++++++
You may install ra2ce using `Docker` and running with different cloud services.
Please refer to our `docker and cloud wiki page <https://github.com/Deltares/ra2ce/wiki/Docker-and-Cloud>`_.


Binder environment
+++++++++++++++++++++++++++
Binder provides us an online web-tool capable of hosting a ``conda`` environment with the latest-greatest version of `RA2CE` already installed and ready to be used.
In this environment you will find all our available examples as well as the possibility to create your own `Jupyter` notebooks.

- Our `ra2ce jupyter-binder <https://mybinder.org/v2/gh/Deltares/ra2ce/jupyter-binder>`_ environment.
- More about `binder <https://mybinder.readthedocs.io/en/latest/>`_.


..
  The following table of contents is hidden as we don't need to display it.
  However, it will bind those items to this one in the "section menu".

.. toctree::
   :caption: Table of Contents
   :maxdepth: 2
   :hidden: