# Purpose of this module

This module contains all the available runners that can be used in this tool.

Each runner is specific for a given analysis type, to decide which one should be picked we make use of a _factory_ (`AnalysisRunnerFactory`).  In addition, you can directly run all available (and supported) analyses for a given configuration (`ConfigWrapper`) simply by doing `AnalysisRunnerFactory.run(config)`.

The result of an analysis runner __execution__ will be a collection of `AnalysisResultWrapper`, an object containing information of the type of analysis ran and its result.

# How to add new analysis?
* Create your own runner which should implement the `AnalysisRunnerProtocol`.
    * Define in the run method how the analysis should be run.
    * If you require extra arguments try using dependency injection while creating the object.
    * You may use the `SimpleAnalysisRunnerBase` to avoid code duplication.
* Implement its selection criteria in the `AnalysisRunnerFactory`.