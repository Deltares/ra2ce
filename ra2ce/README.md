# RA2CE

This package is divided into different (sub-)packages, the most relevants being the following:

- `network`, this (sub-)package contains the logic to retrieve a normalized data structure capable of representing all the required properties of a network for its later analysis.
- `analysis`, this (sub-)package is responsible to execute an analysis (`direct` or `indirect`) for the given network.
- `runners`, this (sub-)package encapsulates the logic to automatize an analysis of a ra2ce model.

Other (sub-)packages carry a more 'supporting' role, such as:

- `common`, a (sub-)package mostly contaning generic definitions as protocols (`typing.Protocol`) to be used across the whole project.
- `configuration`, a (sub-)package responsible to parse the ra2ce `.ini` configuration files (for network and analysis) into their corresponding dataclasses. It is worth mentioning this (sub-) package is explicitely outside `common` to avoid circualr dependencies with the `analysis` and `network` (sub-)packages.

## General class overview

A general overview of the package relationships can be seen in the following diagram.

| ![ra2ce_package_overview.png](/docs/_diagrams/ra2ce_package_overview.png)| 
|:--:| 
| *Ra2ce package overview* |