# Traffic analysis.

In this package all dataclasses, classes and related can be found in order to generate a traffic analysis.
We distinguish two types of analysis:
- Traffic analysis (`TrafficAnalysis`). Provides utilitarian and egalitarian traffic data.
- Equity analysis (`EquityAnalysis`), contains equity data relating regions and their road 'weights'. Provides utilitarian, egalitarian and prioritarian traffic data.

Both analysis are specializations of the base class `TrafficAnalysisBase`, which makes use of an internal dataclass `AccumulatedTraffic` in order to store the intermediate values representing the `regular`, `egalitarian` and `prioritarian` traffic. This dataclass has its `operator.sum` and `operator.mul` overloaded so that we can easily do additions between the acummulated traffic and the calculated one.

To retrieve the correct type of traffic analysis we advise to make use of the `TrafficAnalysisFactory.get_analysis` static method. Said method will return an already initialized analysis based on whether `equity_data` has been provided or not.

In order to load a valid `equity_data` `pd.DataFrame` the user can invoke the `TrafficAnalysisFactory.read_equity_weights` static method.