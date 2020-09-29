# -*- coding: utf-8 -*-
"""
Created on Wed Apr 24 13:29:15 2019

@author: Frederique de Groen

Input: shapefile/OSM/
Output: shapefile with criticality calculated

A general tool for criticality analysis of road networks.

"""

# Modules
from user_input_v2 import setup_analysis, read_input_analyse
import os

# The file structure should be set up like this for the script to work
setup_excel = r".\model_input\analysis_choices.xlsx"
folder_model_input = r".\model_input"
folder_model_output = r".\GIS\output"


def main(args=None):
    print("--------------------- Start analysis ---------------------\n")

    # while loop for the robustness of the tool - the user can input something wrong and try again
    while True:
        try:
            # change location to the root folder of the user
            root_folder = input("Where is your project located? Fill in the path to this folder.\nYour input: ")
            if os.path.exists(root_folder):
                os.chdir(root_folder)
            else:
                print("\nThe path does not exist. Try again to fill in a correct path.")
                continue
        except KeyError:
            print("\nTry again to fill in a correct path.")
            continue
        else:
            break

    while True:
        try:
            batch_analysis = input("\nDo you want to run one or multiple analyses (in batch)? Type 'o' for one or 'm' for multiple.\
                                   \nYour input: ")
            if batch_analysis == "o":
                batch = False
                # the user has chosen to run one analysis
                while True:
                    try:
                        excel_created = input("\nDo you want to create a new analysis excel sheet or use an existing one? Type 'n' for a new one or 'e' for an existing one.\
                                              \nYour input: ")
                        # excel_created = "e"
                        if excel_created == "n":
                            # Ask the user for input for what analysis should be done
                            setup_analysis(setup_excel, folder_model_input, root_folder)
                            input_excels = ["to_fill_in"]
                        elif excel_created == "e":
                            name_input_excel = input(
                                "\nWhat is the name of the excel you want to use in the 'model_input' folder? No file extension needed.\nYour input: ")
                            # name_input_excel = 'to_fill_in'
                            os.path.exists(os.path.join(root_folder, name_input_excel, ".xlsx"))
                            input_excels = [name_input_excel]
                        else:
                            print("\nTry again to fill in the correct input.")
                            continue
                    except ValueError:
                        print("\nTry again to fill in the correct input.")
                        continue
                    else:
                        break
            elif batch_analysis == "m":
                # the user has chosen to run multiple analyses
                batch_excels = input("\nWhat are the names of the excel sheets that you want to use as input? Please separate the names by comma, no file extension is needed. These names will also be used as the names of the output files.\nYour input: ")
                input_excels = batch_excels.replace(" ", "").split(",")
                batch = True
            else:
                print("\nTry again to fill in the correct input.")
                continue
        except ValueError:
            print("\nTry again to fill in the correct input.")
            continue
        else:
            break

    # Read the filled in excel
    for input_excel in input_excels:
        read_input_analyse(folder_model_input, folder_model_output, root_folder, input_excel, batch=batch)


if __name__ == "__main__":
    main()
