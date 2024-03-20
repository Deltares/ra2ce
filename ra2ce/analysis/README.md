# Analysis

This module contains all protocols and classes related to performing an analysis on a graph or network.
Analyses can be identified as:
- `direct`: calculating the **damages** to the infrastructure (roads) due to a hazard (e.g. flood),
- `indirect`: calculating the economical **losses** that are a consequence of the damage to the infrastructure.

## Input and output
An analysis consumes an `AnalysisInputWrapper`, containing analysis parameters, the graph/network and some additional settings.
The `AnalysisRunner` stores the output of an analysis in an `AnalysisResultWrapper`, containing the analysis result (`GeoDataFrame`) and again the analysis parameters.
This output can be exported to different formats using the `AnalysisResultWrapperExporter`.