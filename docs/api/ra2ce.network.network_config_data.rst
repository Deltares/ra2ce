ra2ce.network.network\_config\_data package
===========================================

Enums
-----

.. toctree::
   :maxdepth: 2

   ra2ce.network.network_config_data.enums


Classes
-------

.. autoclass:: ra2ce.network.network_config_data.network_config_data.NetworkSection
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: directed, source, primary_file, diversion_file, file_id, link_type_column, polygon, network_type, road_types, attributes_to_exclude_in_simplification, save_gpkg

.. autoclass:: ra2ce.network.network_config_data.network_config_data.HazardSection
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: hazard_map, hazard_id, hazard_field_name, aggregate_wl, hazard_crs, overlay_segmented_network

.. autoclass:: ra2ce.network.network_config_data.network_config_data.CleanupSection
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: snapping_threshold, pruning_threshold, segmentation_length, merge_lines, cut_at_intersections, delete_duplicate_nodes

.. autoclass:: ra2ce.network.network_config_data.network_config_data.OriginsDestinationsSection
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: origins, destinations, origins_names, destinations_names, id_name_origin_destination, origin_count, origin_out_fraction, category, region, region_var

.. autoclass:: ra2ce.network.network_config_data.network_config_data.IsolationSection
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: locations

.. autoclass:: ra2ce.network.network_config_data.network_config_data.ProjectSection
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: name

.. autoclass:: ra2ce.network.network_config_data.network_config_data.NetworkConfigData
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: root_path, input_path, output_path, static_path, crs, project, network, origins_destinations, isolation, hazard, cleanup
