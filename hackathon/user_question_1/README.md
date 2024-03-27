# User question 1

U.Q.1: Which roads are most likely to get hit by flooding from this hurricane given its projected flood maps?

## Input

- Collection of hazard files in `.tif` format.
- Boundary box (coordinates) of the network extent.
- ra2ce network configuratino file in `.ini` file.

## Pre-processing

### Re-projecting

It might be possible that we require to pre-process the hazard files due to a different projection than WGS-84.

This can be done either locally or "in the cloud".

### Creating the buckets

We create buckets online with each containing our network configuration, network extent and only one hazard file. This way we spread the computation of each hazard overlay for enhanced performance.

## Processing

### Running the hazard overlay

In each bucket, we do a simple ra2ce run by modifying the `NetworkConfigData.hazard.hazard_map` property so that instead of having 'n' defined hazard files, contains only the name of the available hazard file for its executing "bucket".

## Post-processing

### Unifying the outputs

Because we ran ra2ce with one container per hazard file, it means we have our output spread over different containers. We then unify all the available outputs and export its content into both a `.json` (geojson) and a `.feather` file.

## Visualizing

Last, we can now manually download the results ( `.json` and `.feather`) and visualize them locally.