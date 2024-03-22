# Analysis

This module contains all protocols and classes related to performing an analysis on a graph or network.
Analyses can be identified as:
- `direct`: calculating the **damages** to the infrastructure (roads) due to a hazard (e.g. flood),
- `indirect`: calculating the economical **losses** that are a consequence of the damage to the infrastructure.
Each analysis should comply to the `AnalysisProtocol`.

## Configuration
The analyses can be configured in `analysis.ini` or directly in an `AnalysisConfigData` object.

## Lifecycle
An analysis is instantiated by the `AnalysisRunner` via the `AnalysisFactory` and added to an `AnalysisCollection`.
Then the `AnalysisRunner` runs the analyses in the `AnalysisCollection`.

_Add diagram_

## Input/output
An analysis consumes an `AnalysisInputWrapper`, containing analysis parameters from the configuration, the graph/network and some additional settings.
The `AnalysisRunner` stores the output of an analysis in an `AnalysisResultWrapper`, containing the analysis result (`GeoDataFrame`) and again the analysis parameters.
This output can be exported to different formats using the `AnalysisResultWrapperExporter`.

## Overview of analyses
_TODO_