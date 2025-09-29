ra2ce.analysis.analysis\_config\_data package
=============================================

Enums
-----

.. toctree::
   :maxdepth: 2

   ra2ce.analysis.analysis_config_data.enums

Classes
-------

.. autoclass:: ra2ce.analysis.analysis_config_data.analysis_config_data.ProjectSection
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: name

.. autoclass:: ra2ce.analysis.analysis_config_data.analysis_config_data.AnalysisSectionBase
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: name, save_gpkg, save_csv

.. autoclass:: ra2ce.analysis.analysis_config_data.analysis_config_data.AnalysisSectionLosses
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: analysis, weighing, production_loss_per_capita_per_hour, traffic_period, hours_per_traffic_period, trip_purposes, resilience_curves_file, traffic_intensities_file, values_of_time_file, threshold, threshold_destinations, equity_weight, calculate_route_without_disruption, buffer_meters, category_field_name, save_traffic, event_type, risk_calculation_mode, risk_calculation_year

.. autoclass:: ra2ce.analysis.analysis_config_data.analysis_config_data.AnalysisSectionDamages
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: analysis, representative_damage_percentage, event_type, damage_curve, risk_calculation_mode, risk_calculation_year, create_table, file_name

.. autoclass:: ra2ce.analysis.analysis_config_data.analysis_config_data.AnalysisSectionAdaptation
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: analysis, losses_analysis, time_horizon, discount_rate, initial_frequency, climate_factor, hazard_fraction_cost, adaptation_options

.. autoclass:: ra2ce.analysis.analysis_config_data.analysis_config_data.AnalysisSectionAdaptationOption
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: id, name, construction_cost, construction_interval, maintenance_cost, maintenance_interval

.. autoclass:: ra2ce.analysis.analysis_config_data.analysis_config_data.AnalysisConfigData
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: root_path, input_path, output_path, static_path, project, analyses, origins_destinations, network, aggregate_wl, hazard_names



