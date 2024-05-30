# RA2CE

## Ra2ce semantics

- `ra2ce` is a [package](https://packaging.python.org/en/latest/tutorials/packaging-projects/),
- everything else with an `__init__.py` is a subpackage (often written as (sub-)package).
- single `.py` files are [modules](https://docs.python.org/3/tutorial/modules.html),
- from a business perspective an `analysis` might be a module, but technically it can be implemented either as a (subpackage) or a module.

## Structure description

This package is divided into different (sub-)packages, the most relevants being the following:

- `network`, this (sub-)package contains the logic to retrieve a normalized data structure capable of representing all the required properties of a network for its later analysis.
- `analysis`, this (sub-)package is responsible to execute an analysis (`damages` or `losses`) for the given network.
- `runners`, this (sub-)package encapsulates the logic to automatize an analysis of a ra2ce model.

Other (sub-)packages carry a more 'supporting' role, such as:

- `common`, a (sub-)package mostly contaning generic definitions as protocols (`typing.Protocol`) to be used across the whole project.
- `configuration`, a subpackage responsible to parse the ra2ce `.ini` configuration files (for network and analysis) into their corresponding dataclasses. It is worth mentioning this subpackage is explicitely outside `common` to avoid circular dependencies with the `analysis` and `network` subpackages.

## General class overview

A general overview of the package relationships can be seen in the following diagram.

| ![ra2ce_package_overview.drawio.png](/docs/_diagrams/ra2ce_package_overview.drawio.png)| 
|:--:| 
| *Ra2ce package overview* |