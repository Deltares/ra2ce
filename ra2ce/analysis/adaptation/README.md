# Adaptation
The subpackage `ra2ce.analysis.adapatation` contains all classes related to an adaptation analysis.

![image](../../../docs/_diagrams/adaptation_class.drawio.png)

An `Adaptation` analysis calculates the **BC-ratio** (benefits divided by the costs) of given adaptation option on the infrastructure.
The `AdaptionOption`s are listed in attribute `all_options`, where the first entry is the `reference_option` (situation in which no adaptation is done, also known as "business as usual").

The `AdaptationOption` contains the `AdaptationSettings`, which contains various properties that are relevant for the calculations:
- `discount_rate`: inflation correction on the cost
- `time_horizon`: the period for which the analysis is done
- `initial_frequency`: current expected frequency of the hazard
- `climate_factor`: correction on the frequency of the hazard due to climate changes

These properties are configured in `AnalysisConfigData.AdaptationConfigData`.

## Benefit calculation
The benefit of a certain adaptation option (`AdapatationOption`) is calculated by subtracting the impact of the option from the impact of the reference option.
It is expected that the impact of a certain adaptation option is smaller than the impact of the reference option, resulting in a positive benefit.

### Impact
The impact of an option is calculated by determining the cost of the different analyses (damages and/or losses) that are caused by a certain hazard.
Which losses analysis is run is determined by `AnalysisConfigData.AdaptationConfigData.losses_analysis`.

The configuration of the damages and the losses analyses are derived from their standard configuration in the section `DamagesConfigData` and `LossesAnalysisConfigDataProtocol`, which are stored in `AdaptationOptionAnalysis` for a specific option.
One of these needs to be configured.

In `AdaptationOptionAnalysis.get_analysis_info` it can be found which analysis to run.
Note this logic resembles the logic in `AnalysisFactory`, which can't be used due to circular dependencies.
Here also a regex expression is given to find the right column in the analysis result.

The event impact is calculated by summing the damages and/or the losses per link.
Based on this the net present impact is calculated, taking into account the `initial_frequency` corrected by a `climate_factor`, and the `time_horizon` and `discount_rate`.

## Cost calculation
The cost of an adaptation is calculated per link in the network by multiplying the unit cost of an adaptation with the length of the link.
In case `hazard_fraction_cost` is True, the cost is multiplied by the impacted fraction of the link.

### Unit cost
The unit cost (cost \[€\] per unit \[m\] of the infrastructure) is calculated from 2 components:
- construction cost at a construction time interval
- maintenance cost at a maintenance time interval

To get the net present unit cost, the `time_horizon` and `discount_rate` are taken into account.

Both of these components can be omitted, assuming there is no construction or maintenance involved.

These components are configured per option in `AnalysisConfigData.AdaptationOptionConfigData`, where also the **unique** id and the name of the adaptation are given.

## Remarks
The inputs to the damages (e.g. damage functions) and losses (e.g. resilience curves) analysis should be put in folder `input/{id}/{analysis}/input`, where `id` is the id of the `AdaptationOption` and analysis is the `config_value` of `AdaptationOptionAnalysis.analysis_type`.

If the adaptation workflow is run from the handler, the damages and losses analysis are run separately as well.
