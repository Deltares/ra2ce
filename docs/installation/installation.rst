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
::
  pip install git+https://github.com/Deltares/ra2ce.git
::

Alternatively you can install a specific tag or commit hash from our repo by using the symbol `@`:
::
  pip install git+https://github.com/Deltares/ra2ce.git@v0.3.1
::

Development mode
+++++++++++++++++++++++++++
When running a development environment with Anaconda, the user may follow these steps in command line:
::
  cd <to the main repository RA2CE folder>
  conda env create -f .config\environment.yml
  conda activate ra2ce_env
  poetry install
::
