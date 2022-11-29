import logging
from pathlib import Path

import pandas as pd

from ra2ce.analyses.direct.damage.damage_fraction_uniform import DamageFractionUniform
from ra2ce.analyses.direct.damage.damage_function_base import DamageFunctionBase
from ra2ce.analyses.direct.damage.max_damage import MaxDamageByRoadTypeByLane


class DamageFunctionByRoadTypeByLane(DamageFunctionBase):
    """
    A damage function that has different max damages per road type, but a uniform damage_fraction curve


    The attributes need to be of the type:
    self.max_damage (MaxDamage_byRoadType_byLane)
    self.damage_fraction (DamageFractionHazardSeverityUniform)

    """

    def __init__(
        self,
        max_damage=None,
        damage_fraction=None,
        name=None,
        hazard="flood",
        type="depth_damage",
        infra_type="road",
    ):
        # Construct using the parent class __init__
        super().__init__(
            max_damage=max_damage,
            damage_fraction=damage_fraction,
            name=name,
            hazard=hazard,
            type=type,
            infra_type=infra_type,
        )
        # Do extra stuffs

    def from_input_folder(self, folder_path):
        """Construct a set of damage functions from csv files located in the folder_path

        Arguments:
            *folder_path* (Pathlib Path) : path to folder where csv files can be found
        """

        def find_unique_csv_file(folder_path: Path, part_of_filename: str) -> Path:
            """
            Find unique csv file in a folder, with a given part_of_filename
            Raises a warning if no file can be found, and an error if more than one file is found
            """
            result = []
            for file in folder_path.iterdir():
                if (part_of_filename in file.stem) and (file.suffix == ".csv"):
                    result.append(file)
            if len(result) > 1:
                raise ValueError(
                    "Found more then one damage file in {}".format(folder_path)
                )
            elif len(result) == 0:
                logging.warning(
                    "Did not found any damage file in {}".format(folder_path)
                )
            else:
                result = result[0]
            return result

        # Load the max_damage object
        max_damage = MaxDamageByRoadTypeByLane()
        max_dam_path = find_unique_csv_file(folder_path, "max_damage")
        max_damage.from_csv(max_dam_path, sep=";")

        self.max_damage = max_damage

        # Load the damage fraction function
        # search in the folder for something *damage_fraction
        damage_fraction = DamageFractionUniform()
        dam_fraction_path = find_unique_csv_file(folder_path, "hazard_severity")
        damage_fraction.from_csv(dam_fraction_path, sep=";")
        self.damage_fraction = damage_fraction

        damage_fraction.create_interpolator()

    # Todo: these two below functions are maybe better implemented at a lower level?
    def add_max_damage(self, df, prefix=None):
        """ "Ads the max damage value to the dataframe"""
        cols = df.columns
        assert "road_type" in cols, "no column 'road type' in df"
        assert "lanes" in cols, "no column 'lanes in df"

        max_damage_data = self.max_damage.data
        df["{}_temp_max_dam".format(prefix)] = max_damage_data.lookup(
            df["road_type"], df["lanes"]
        )
        return df

    def calculate_damage(
        self, df=pd.DataFrame, DamFun_prefix=str, hazard_prefix=str, event_prefix=str
    ) -> pd.DataFrame:
        """Calculates the damage for one event

        The prefixes are used to find/set the right df columns

        Arguments:
            *df* (pd.Dataframe) : dataframe with road network data
            *DamFun_prefix* : prefix to identify the right damage function e.g. 'A'
            *hazard_prefix* : prefix to identify the right hazard e.g. 'F'
            *event_prefix*  : prefix to identify the right event, e.g. 'EV1'

        Returns:
            *df* (pd.DataFrame) : dataframe data with the damage calculation added as new column

        """

        interpolator = (
            self.damage_fraction.interpolator
        )  # get the interpolator function

        # Find correct columns in dataframe
        result_col = "dam_{}_{}".format(event_prefix, DamFun_prefix)
        max_dam_col = "{}_temp_max_dam".format(DamFun_prefix)
        hazard_severity_col = "{}_{}_me".format(
            hazard_prefix, event_prefix
        )  # mean is hardcoded now
        hazard_fraction_col = "{}_{}_fr".format(
            hazard_prefix, event_prefix
        )  # fraction column is hardcoded

        df[result_col] = round(
            df[max_dam_col].astype(float)  # max damage (euro/m)
            * interpolator(df[hazard_severity_col].astype(float))  # damage curve  (-)
            * df["length"]  # segment length (m)
            * df[hazard_fraction_col],
            0,
        )  # round to whole numbers
        return df
