.. _installation:

Installation
============

RA2CE can be operated via the command-line interface with two commands. 
Before RA2CE can be used, the correct Python environment needs to be installed 
(see *environment.yml*). Anaconda is a well-known environment manager for Python 
and can be used to install the correct environment and run RA2CE via its 
command-line interface. It is recommended to install Anaconda, instead of 
`miniconda`, so that you have all required packages already available during the 
following steps.


CLI only
+++++++++++++++++++++++++++
If only interested in using the tool via command-line interface follow these steps:

  .. code-block:: bash

    pip install ra2ce
  
Alternatively you can install the latest version available on GitHub or a specific tag / commit hash by using the symbol `@`:

  .. code-block:: bash

    pip install git+https://github.com/Deltares/ra2ce.git
    pip install git+https://github.com/Deltares/ra2ce.git@v0.3.1


.. _install_ra2ce_devmode:

Development mode
+++++++++++++++++++++++++++
When running a development environment with Anaconda, the user may follow these steps in command line:

  .. code-block:: bash

    cd <to the main repository RA2CE folder>
    conda env create -f .config\environment.yml
    conda activate ra2ce_env
    poetry install


Docker and cloud
+++++++++++++++++++++++++++
You may install ra2ce using `Docker` and running with different cloud services.
Please refer to our :ref:`docker_and_cloud`.


Binder environment
+++++++++++++++++++++++++++
Binder provides us an online web-tool capable of hosting a ``conda`` environment with the latest-greatest version of `RA2CE` already installed and ready to be used.
In this environment you will find all our available examples as well as the possibility to create your own `Jupyter` notebooks or experiment with the `CLI` options.

- Our `ra2ce jupyter-binder <https://mybinder.org/v2/gh/Deltares/ra2ce/jupyter-binder>`_ environment.
- More about `binder <https://mybinder.readthedocs.io/en/latest/>`_.


..
  The following table of contents is hidden as we don't need to display it.
  However, it will bind those items to this one in the "section menu".

.. toctree::
   :caption: Table of Contents
   :maxdepth: 2
   :hidden: