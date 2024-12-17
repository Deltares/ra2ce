[![Python 3.11](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/downloads/release/python-31110/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![TeamCity build status](https://dpcbuild.deltares.nl/app/rest/builds/buildType:id:Ra2ce_Ra2ceContinuousDelivery_RunAllTests/statusIcon.svg)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Deltares_ra2ce&metric=alert_status&token=35cd897258b4c3017a42077f18304e6a73042dd6)](https://sonarcloud.io/summary/new_code?id=Deltares_ra2ce)
[![GitHub Pages documentation](https://github.com/Deltares/ra2ce/actions/workflows/deploy_docs.yml/badge.svg)](https://github.com/Deltares/ra2ce/actions/workflows/deploy_docs.yml)
[![Binder branch](https://github.com/Deltares/ra2ce/actions/workflows/binder_branch.yml/badge.svg)](https://github.com/Deltares/ra2ce/actions/workflows/binder_branch.yml)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Deltares/ra2ce/jupyter-binder)


![RA2CE](./docs/_resources/ra2ce_banner.png "Ra2ce banner")

This is the repository of RA2CE (*just say race!*) - the Resilience Assessment and Adaptation for Critical infrastructurE Toolkit Python Package developed by Deltares. RA2CE helps to quantify resilience of critical infrastructure networks, prioritize interventions and adaptation measures and select the most appropriate action perspective to increase resilience considering future conditions.

**Contact** Margreet van Marle (Margreet.vanMarle@Deltares.nl)

Find more about the following topics in our [official documentation page](https://deltares.github.io/ra2ce/):

- [Contributing](https://deltares.github.io/ra2ce/contributing/index.html)
- [Installation](https://deltares.github.io/ra2ce/installation/installation.html)
- [Network user guide](https://deltares.github.io/ra2ce/network_module/network_module.html)
- [Analysis user guide](https://deltares.github.io/ra2ce/analysis_module/analysis_module.html)

## Distribution
Ra2ce is shared with [GPL3 license](https://www.gnu.org/licenses/gpl-3.0.en.html), you may use and/or extend it by using the same license. For specific agreements we urge you to contact us.

## Usage
If you wish to run ra2ce locally we recommend to have a look at the [installation section](#installation). 
On the other hand, if you wish to run a preinstalled environment, you may use our [examples in binder](examples/README.md).

## Third-party Notices
This project incorporates components from the projects listed below.

**NetworkX**: NetworkX is distributed with the [3-clause BSD license](https://opensource.org/license/bsd-3-clause/).

   > Copyright (C) 2004-2022, NetworkX Developers
   Aric Hagberg <hagberg@lanl.gov>
   Dan Schult <dschult@colgate.edu>
   Pieter Swart <swart@lanl.gov>
   All rights reserved.

**OSMnx**: OSMnx is distributed under the [MIT License](https://opensource.org/license/mit/).

  > Boeing, G. 2017. 
  [OSMnx: New Methods for Acquiring, Constructing, Analyzing, and Visualizing Complex Street Networks](https://geoffboeing.com/publications/osmnx-complex-street-networks/)
  Computers, Environment and Urban Systems 65, 126-139. doi:10.1016/j.compenvurbsys.2017.05.004
