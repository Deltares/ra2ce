# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 15:10:12 2019

@author: Frederique de Groen

Part of a general tool for criticality analysis of networks.

"""

# Modules
import pandas as pd
import os
from analyses_v2 import single_link_alternative_routes, \
    single_link_alternative_routes_graph, multi_link_alternative_routes, \
    single_link_access_routes, multi_link_access_routes, single_link_europe, \
    multi_link_od_matrix, multi_link_alternative_routes_graph, multi_link_od_matrix_graph
import time
from network_functions_v2 import get_graph_from_polygon, create_graph_europe


# Functions
def setup_analysis(SetupExcel, FolderModelInput, RootFolder):
    """Setup the excel that is used for analysis input
    """
    choices_excel = pd.read_excel(SetupExcel)
    create_excel = pd.DataFrame(columns=['analysis', 'links_analysis', 'input_data'])
    ask_for_road_usage = True  # a switching variable

    for question, column in enumerate(list(choices_excel.columns)[1:-1]):
        # ask the user for input for each column in the excel
        while True:
            try:
                ### ASK THE QUESTION AND DISPLAY OPTIONS ###
                to_ask = column.replace('_', ' ')
                input_options = [i for i in choices_excel[column] if isinstance(i, str)]
                input_options_text = dict(zip(list(range(0, len(input_options)+1)), input_options))
                print("\n", choices_excel.loc[question, 'questions'], sep='')
                print("\nType the number of your choice and press enter. The options are:\n".format(to_ask))
                for k, v in input_options_text.items():
                    print("  {}. {}\n".format(k, v))
                the_input = input("Your input: ")

                ### FORMAT AND SHOW THE ANSWER ###
                if ',' in the_input:
                    the_input = [int(a) for a in the_input.split(",")]
                else:
                    the_input = int(the_input)
                print("\n**************************************\nYou successfully chose: ")

                list_input = []
                if isinstance(the_input, list):
                    for i in the_input:
                        print("'{}'".format(input_options_text[i]))
                        list_input.append(input_options_text[i])
                else:
                    print("'{}'".format(input_options_text[the_input]))

                ### PROCESS THE ANSWER ###
                if isinstance(the_input, int):
                    if input_options_text[the_input] == 'Download graph from OSM':
                        # print informative text
                        with open(os.path.join(RootFolder, './tool_text/text_osm_network_types.txt'), 'r') as file:
                            text_osm_network_types = file.read()
                        with open(os.path.join(RootFolder, './tool_text/text_osm_road_types.txt'), 'r') as file:
                            text_osm_road_types = file.read()
                        print("\n", text_osm_road_types)
                        print("\n", text_osm_network_types)

                        create_excel.drop(columns=['input_data'], inplace=True)
                        add_columns = pd.read_csv(os.path.join(RootFolder, "tool_text/download_graph_osm.csv"), sep=';')
                        create_excel = pd.concat([create_excel, add_columns], axis=1)
                        break
                    elif input_options_text[the_input] == 'OSM Europe including floods':
                        # print informative text
                        with open(os.path.join(RootFolder, './tool_text/text_create_graph_europe.txt'), 'r') as file:
                            text_load_existing_graph = file.read()
                        print('\n', text_load_existing_graph)

                        create_excel.drop(columns=['input_data'], inplace=True)  # TODO: bit quick and dirty solution
                        add_columns = pd.read_csv(os.path.join(RootFolder, "tool_text/create_graph_europe.csv"), sep=';')
                        create_excel = pd.concat([create_excel, add_columns], axis=1)
                        break

                # if the input is correct, it is saved in a new dataframe
                if column in ['hazard_data', 'input_data']:
                    # for the columns hazard_data and input_roads a new column is created for the input
                    if input_options_text[the_input] == 'Shapefiles for Analysis and Shapefiles for Diversion':
                        # create separate cells for analysis shapefiles and diversion shapefiles
                        to_input = ['Shapefiles for Analysis', 'Shapefiles for Diversion']
                        for i in to_input:
                            create_excel.loc[len(create_excel['input_data'].value_counts()), column] = i
                    elif isinstance(the_input, list):
                        for i in the_input:
                            create_excel.loc[len(create_excel['input_data'].value_counts()), column] = input_options_text[i]
                    else:
                        create_excel.loc[len(create_excel['input_data'].value_counts()), column] = input_options_text[the_input]
                elif column in create_excel:
                    # the column is already in the excel
                    if isinstance(the_input, list):
                        for i in list_input:
                            create_excel.loc[len(create_excel[column].value_counts()), column] = i
                    else:
                        create_excel.loc[len(create_excel[column].value_counts()), column] = input_options_text[the_input]
                else:
                    if isinstance(the_input, list):
                        for n, i in enumerate(the_input):
                            create_excel.loc[n, column] = input_options_text[i]
                    else:
                        create_excel.loc[0, column] = input_options_text[the_input]

            except KeyError:
                print('\nTry again to fill in a correct number.')
                continue

            else:
                break

        # break out of the for-loop if this happens:
        if isinstance(the_input, int):
            if input_options_text[the_input] in ['Download graph from OSM', 'OSM Europe including floods']:
                ask_for_road_usage = False
                break

    if ask_for_road_usage:
        create_excel.insert(3, 'file_names', '<name of the file(s) (no extension), if multiple, separate by comma>')
        if create_excel.iloc[0]['data_manipulation'] == 'None':
            create_excel.drop(columns=['data_manipulation'], inplace=True)
        else:
            create_excel['thresholds'] = '<threshold for data manipulation>'

        # Ask the user if they have enough data to calculate damage costs with AADT, basic vehicle operating costs,
        # persons per vehicle and/or no detour cost
        while True:
            try:
                the_input = input("\nDo you have information on the road usage? E.g. annual average daily traffic per traffic classification. Type 'y' for yes or 'n' for no.\nYour input: ")
                if the_input == 'y':
                    the_input = input("\nDo you already have this information stored in a file in the folder 'model_input'? Type 'y' for yes or 'n' for no.\nYour input: ")
                    if the_input == 'y':
                        # the user has the input files stored in the right folder, now check if the name of that file is correct
                        the_input = input("\nIs the information stored in 'road_usage.xlsx'? Type 'y' for yes or 'n' for no.\nYour input: ")
                        if the_input == 'y':
                            if 'road_usage.xlsx' in os.listdir(os.path.join(RootFolder, 'model_input/')):
                                print("\nThe file 'road_usage.xlsx' is found and will be used for the analysis.")
                                if "road usage data" not in list(create_excel['input_data']):
                                    create_excel.loc[len(create_excel) + 1, 'input_data'] = "road usage data"
                                    create_excel.loc[create_excel['input_data'] == "road usage data", 'file_names'] = "road_usage"
                            else:
                                print("\nThe file is not found. Please provide the right information.")
                                continue
                        elif the_input == 'n':
                            the_input = input("\nWhat is the name of the excel file in the folder 'model_input' that you want to use? Type the name of the file without extension.\nYour input: ")
                            if '{}.xlsx'.format(the_input) in os.listdir(os.path.join(RootFolder, 'model_input/')):
                                print("\nThe file '{}.xlsx' is found and will be used for the analysis.".format(the_input))
                                create_excel.loc[len(create_excel)+1, 'input_data'] = "road usage data"
                                create_excel.loc[create_excel['input_data'] == "road usage data", 'file_names'] = the_input
                            else:
                                print("\nThe file is not found. Please provide the right information.")
                                continue
                    elif the_input == 'n':
                        # the user wants to create an excel where he/she can input the data into
                        # print informative text
                        with open(os.path.join(RootFolder, './tool_text/text_road_usage.txt'), 'r') as file:
                            text_road_usage = file.read()
                        the_input = input(text_road_usage)

                        if the_input == 'A':
                            road_usage_df = pd.DataFrame(data={'vehicle_type': range(1, 9), 'attribute_name': '<fill in>', 'operating_cost': '<fill in>'})
                        elif the_input == 'B':
                            road_usage_df = pd.DataFrame(data={'vehicle_type': range(1, 9), 'attribute_name': '<fill in>', 'passengers_w_driver': '<fill in>', 'daily_loss_disruption': '<fill in>'})
                        elif the_input == 'AB':
                            road_usage_df = pd.DataFrame(data={'vehicle_type': range(1, 9), 'attribute_name': '<fill in>', 'operating_cost': '<fill in>', 'passengers_w_driver': '<fill in>', 'daily_loss_disruption': '<fill in>'})
                        elif the_input == 'exit':
                            # the user realised it did not have all the data necessary, so exit the loop
                            break
                        else:
                            print("\nYou did not write down any of the options. Please fill in one of the correct options.")
                            continue

                        # save the name of the file to the general setup excel file for the analysis
                        create_excel.loc[len(create_excel)+1, 'input_data'] = "road usage data"
                        create_excel.loc[create_excel['input_data'] == "road usage data", 'file_names'] = "road_usage"

                        # save the dataframe to an excel and let the user fill in the excel
                        save_name = os.path.join(FolderModelInput, 'road_usage.xlsx')
                        road_usage_df.to_excel(save_name)
                        os.startfile(save_name)  # open the excel file

                        # ask the user to only continue if the excel is filled in correctly
                        print("\nThe excel sheet for road usage input opens..")
                        time.sleep(2)
                        input("\nPress Enter if you have correctly filled in the excel.")
                elif the_input == 'n':
                    # the user does not have any extra information, exit this while loop and continue
                    break
                else:
                    print("\nTry again to fill in the question correcty. Please fill in 'y' for yes or 'n' for no.")
                    continue
            except KeyError:
                print("\nTry again to fill in the questions correctly.")
                continue
            else:
                break
    else:
        # wait a bit for the user to read the text before opening the excel
        time.sleep(3)

    # add a field for the name of the id column in the input shapefile(s)
    if 'input_data' in create_excel.columns:
        if 'Shapefiles for Analysis' in list(create_excel['input_data']):
            create_excel.loc[len(create_excel['input_data'])+1, 'input_data'] = 'name of ID column'
            create_excel.loc[create_excel['input_data'] == 'name of ID column', 'file_names'] = '<ID column name>'

    # remove the columns that are not used
    if "No data" in list(create_excel['hazard_data']):
        create_excel.drop(columns=['hazard_data'], inplace=True)

    if "No, thanks" in list(create_excel['economic_assessment']):
        create_excel.drop(columns=['economic_assessment'], inplace=True)

    if 'hazard_data' in create_excel.columns:
        create_excel.drop(columns=['hazard_data'], inplace=True)
        while True:
            try:
                input_hazard = input("\nCan the hazard data be joined with the roads by ID or spatially? Type 'i' for joining by ID or 's' for joining spatially.\nYour input: ")
                if input_hazard == 'i':
                    add_columns = pd.read_csv(os.path.join(RootFolder, "tool_text/hazard_input_join_by_id.csv"), sep=';')
                    create_excel = create_excel.append(add_columns, ignore_index=True, sort=False)
                elif input_hazard == 's':
                    add_columns = pd.read_csv(os.path.join(RootFolder, "tool_text/hazard_input_join_spatial.csv"),
                                              sep=';')
                    create_excel = create_excel.append(add_columns,
                        ignore_index=True, sort=False)
            except KeyError:
                print("\nTry again to fill in a correct letter.")
                continue
            else:
                break

    if 'Multi-link Disruption (2): Calculate the disruption for an Origin/Destination matrix' in list(create_excel['links_analysis']):
        add_columns = pd.read_csv(os.path.join(RootFolder, "tool_text/od_pair_input.csv"), sep=';')
        create_excel = create_excel.append(add_columns, ignore_index=True, sort=False)

    # save as excel
    save_name = os.path.join(FolderModelInput, 'to_fill_in.xlsx')
    while True:
        try:
            create_excel.to_excel(save_name)
            os.startfile(save_name)  # open the excel file
        except PermissionError as e:
            print("An excel file in the folder 'model_input' with the name 'to_fill_in' is open. Close it and the Excel will open automatically. Error: {}".format(e))
            continue
        else:
            break

    # ask the user to only continue if the excel is filled in correctly
    print("\nThe excel sheet for the general input for the analysis opens..")
    time.sleep(3)
    input("Press Enter if you have correctly filled in the excel.")


def read_input_analyse(FolderModelInput, FolderModelOutput, RootFolder, NameInputExcel, batch=False):
    """
    This function reads the input excel and points to the right analysis.
    FolderModelInput: full path of the folder where the model input is stored.
    FolderModelOutput: full path of the folder where the model output should be stored.
    """
    # Ask the user for the name of the analysis
    if not batch:
        input_name = input("\nWhat name do you want to give to the analysis?\nYour input: ")
    else:
        input_name = NameInputExcel

    print("\nRunning calculation '{}'.".format(input_name))

    df = pd.read_excel(os.path.join(FolderModelInput, '{}.xlsx'.format(NameInputExcel)))
    # CRS must be in EPSG:4326
    crs_ = 4326

    if 'shapefile_for_OSM' in df.columns:
        # When the user chooses to download a graph from OSM, they can only do the alternative distance analysis
        # download the graph from OSM with the data from the user and calculate the shortest paths
        path_shp = os.path.join(RootFolder, 'GIS/input/', '{}.shp'.format(df.iloc[0]['shapefile_for_OSM']))
        network_type = df.iloc[0]['network_type'].lower()
        road_types = df.iloc[0]['road_types']

        if 'input_data' in df.columns:
            if "path to hazard data (multiple separated by comma)" in list(df['input_data']):
                hazard_data = {'path': [os.path.join(RootFolder, 'GIS/input/', x) for x in df.loc[df['input_data'] == "path to hazard data (multiple separated by comma)", 'file_names'].iloc[0].split(",")],
                               'attribute_name': [x for x in df.loc[df['input_data'] == "attribute name(s) of hazard data (name of shapefile attribute or name that you want to give)", 'file_names'].iloc[0].split(",")],
                               'aggregation': df.loc[df['input_data'] == 'aggregation method', 'file_names'].iloc[0],
                               'threshold': df.loc[df['input_data'] == 'threshold value', 'file_names'].iloc[0]}

        if network_type in ['drive', 'drive_service', 'all', 'all_private']:
            # only drivable roads have a choice between road types
            road_types = road_types.lower().replace(',', '|')  # OSMNX takes the '|' sign as 'and' operator

        G = get_graph_from_polygon(path_shp, network_type, road_types)

        if 'Single-link Disruption' in list(df['links_analysis']):
            single_link_alternative_routes_graph(input_name, FolderModelOutput, G, crs_)
        elif 'Multi-link Disruption (1): Calculate the disruption for all damaged roads' in list(df['links_analysis']):
            multi_link_alternative_routes_graph(input_name, FolderModelOutput, G, crs_, hazard_data)
        elif "Multi-link Disruption (2): Calculate the disruption for an Origin/Destination matrix" in list(
                df.links_analysis):
            input_data_dict = create_input_data_dict(df, RootFolder)
            multi_link_od_matrix_graph(input_name, FolderModelOutput, input_data_dict, hazard_data, G, crs_)
        else:
            print("You can only do a Single-link Disruption or Multi-link Disruption (1) analysis with OSM data. Run again and check your input.")

    elif 'clip_polygon_europe' in list(df['input_data']):
        # When the user chooses to use an existing graph (from OSM)
        # Save the paths and choices of the user in a dict
        input_dict = {'incl_nuts': list(df['nuts_3_regions_to_include']),
                      'incl_countries': list(df['country_codes_to_include']),
                      'clip_shp_path': df[df['input_data'] == 'clip_polygon_europe'].iloc[0]['path_to_data'],
                      'floods_path': df[df['input_data'] == 'flood_data_europe'].iloc[0]['path_to_data'],
                      'osm_path': df[df['input_data'] == 'osm_data_europe'].iloc[0]['path_to_data'],
                      'pbf_europe_path': df[df['input_data'] == 'pbf_europe'].iloc[0]['path_to_data'],
                      'nuts_3_regions': df[df['input_data'] == 'nuts_3_regions'].iloc[0]['path_to_data']}

        G = create_graph_europe(RootFolder, FolderModelOutput, input_name, input_dict, crs_)

        if 'Single-link Disruption' in list(df['links_analysis']):
            # Do the single link analysis with the chosen NUTS-3 regions
            single_link_europe(G, FolderModelOutput, input_name, crs_)
        elif 'Multi-link Disruption (1): Calculate the disruption for all damaged roads' in list(df['links_analysis']):
            # Do the multilink analysis with the flood Area of Influence data for Europe
            # multi_link_flood_all(G)
            print("Not yet implemented")
        elif 'Multi-link Disruption (2): Calculate the disruption for an Origin/Destination matrix' in list(df['links_analysis']):
            # Do the Origin Destination matrix calculation. Need to define the origin and destination still?
            multi_link_od_matrix(G, FolderModelOutput, input_dict, 'AoI_rp100', 'val_rp100', 0, crs_)
        else:
            print("Something went wrong.. Run again and check your input.")

    else:
        # Create the input for the analyses - paths to files
        input_data_dict = create_input_data_dict(df, RootFolder)

        snapping_ = False
        snapping_threshold = 0
        pruning_ = False
        pruning_threshold = 0
        hazard_data = {}

        if "data_manipulation" in df.columns:
            if "Snapping" in list(df['data_manipulation']):
                snapping_ = True
                snapping_threshold = df.loc[df['data_manipulation'] == "Snapping", 'thresholds'].iloc[0]

            if "Pruning" in list(df['data_manipulation']):
                pruning_ = True
                pruning_threshold = df.loc[df['data_manipulation'] == "Pruning", 'thresholds']
        if "path to hazard data (multiple separated by comma)" in list(df['input_data']):
            hazard_data['path'] = [os.path.join(RootFolder, 'GIS/input/', x) for x in
                          df.loc[df['input_data'] == "path to hazard data (multiple separated by comma)", 'file_names'].iloc[0].split(",")]
            hazard_data['attribute_name'] = [x for x in df.loc[df['input_data'] == "attribute name(s) of hazard data (name of shapefile attribute or name that you want to give)", 'file_names'].iloc[0].split(",")]
            # for the following items it is variable if they are included in the input excel
            for item in ["aggregation method", "ID name to join with", "threshold value"]:
                if item in list(df['input_data']):
                    hazard_data[item.split(" ")[0]] = df.loc[df['input_data'] == item, 'file_names'].iloc[0]

        # Now, there are 4 types of analyses: alternative routes or access routes
        # combines with single or multiple link. In addition you can add a hazard map
        # to determine the area of roads that do not function anymore.
        if "Alternative Route Finder" in list(df.analysis):
            if "Single-link Disruption" in list(df.links_analysis):
                single_link_alternative_routes(input_name, FolderModelOutput, input_data_dict, crs_,
                                               snapping_, snapping_threshold, pruning_, pruning_threshold)

            elif "Multi-link Disruption (1): Calculate the disruption for all damaged roads" in list(df.links_analysis):
                multi_link_alternative_routes(input_name, FolderModelOutput, input_data_dict, hazard_data, crs_,
                                               snapping_, snapping_threshold, pruning_, pruning_threshold)

            elif "Multi-link Disruption (2): Calculate the disruption for an Origin/Destination matrix" in list(df.links_analysis):
                multi_link_od_matrix(input_name, FolderModelOutput, input_data_dict, hazard_data, crs_,
                                               snapping_, snapping_threshold, pruning_, pruning_threshold)

            else:
                "Something went wrong.. Run again and check your input."

        elif "Accessibility to Key Points of Interest" in list(df.analysis):

            if "Single-link Disruption" in list(df.links_analysis):
                single_link_access_routes()

            elif "Multi-link Disruption" in list(df.links_analysis):
                multi_link_access_routes()


def create_input_data_dict(data, root_folder):
    input_data_dict = {}
    for input_ in data.input_data:
        if input_ == input_:  # check if the input is not empty (nan)
            the_value = data[data['input_data'] == input_].iloc[0]['file_names']
            if the_value == the_value:  # check if the value is not Nan
                if input_ == 'name of ID column':
                    input_data_dict['id_name'] = the_value
                    continue
                if input_ == 'ID name of both origin and destination files':
                    input_data_dict['id_od'] = the_value
                    continue
                key_name1 = '{}_path'.format(input_.replace(' ', '_').lower())
                if isinstance(the_value, str):
                    if ',' in the_value:
                        v_list = []
                        for v in the_value.split(','):
                            if input_ in ['Shapefiles for Analysis', 'Shapefiles for Diversion',
                                          'origin shapefiles', 'destination shapefiles']:
                                v_list.append(os.path.join(root_folder, 'GIS/input/', '{}.shp'.format(v)))
                            elif input_ == 'road usage data':
                                v_list.append(os.path.join(root_folder, 'model_input/', '{}.xlsx'.format(v)))
                            if input_ == 'origin shapefiles':
                                input_data_dict['o_names'] = [x.split('_')[0] for x in the_value.split(',')]
                            if input_ == 'destination shapefiles':
                                input_data_dict['d_names'] = [x.split('_')[0] for x in the_value.split(',')]
                        input_data_dict[key_name1] = v_list
                    else:
                        if input_ in ['Shapefiles for Analysis', 'Shapefiles for Diversion',
                                      'origin shapefiles', 'destination shapefiles']:
                            input_data_dict[key_name1] = os.path.join(root_folder, 'GIS/input/',
                                                                      '{}.shp'.format(the_value))
                        elif input_ == 'road usage data':
                            input_data_dict[key_name1] = os.path.join(root_folder, 'model_input/',
                                                                      '{}.xlsx'.format(the_value))
                        if input_ == 'origin shapefiles':
                            input_data_dict['o_names'] = the_value.split('_')[0]
                        if input_ == 'destination shapefiles':
                            input_data_dict['d_names'] = the_value.split('_')[0]
    return input_data_dict