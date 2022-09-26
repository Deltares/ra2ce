class ManualDamageFunctions:
    """"
    This class keeps an overview of the manual damage functions

    Default behaviour is to find, load and apply all available functions
    At 22 sept 2022: only implemented workflow for DamageFunction_by_RoadType_by_Lane
    """
    def __init__(self):
        self.available = {} #keys = name of the available functions; values = paths to the folder
        self.loaded = [] #List of DamageFunction objects (or child classes

    def find_damage_functions(self,folder) -> None:
        """Find all available damage functions in the specified folder"""
        assert folder.exists(), 'Folder {} does not contain damage functions'.format(folder)
        for subfolder in folder.iterdir(): #Subfolders contain the damage curves
            if subfolder.is_dir():
                #print(subfolder.stem,subfolder)
                self.available[subfolder.stem] = subfolder
        logging.info('Found {} manual damage curves: \n {}'.format(
            len(self.available.keys()),
            list(self.available.keys())))
        return None

    def load_damage_functions(self):
        """"Load damage functions in Ra2Ce"""
        for name, dir in self.available.items():
            damage_function = DamageFunction_by_RoadType_by_Lane(name=name)
            damage_function.from_input_folder(dir)
            damage_function.set_prefix()
            self.loaded.append(damage_function)
            logging.info("Damage function '{}' loaded from folder {}".format(damage_function.name,dir))

class DamageFunction:
    """
    Generic damage function

    """
    def __init__(self, max_damage=None,damage_fraction=None,
                 name=None,hazard='flood',type='depth_damage',infra_type='road'):
        self.name = name
        self.hazard = hazard
        self.type = type
        self.infra_type = infra_type
        self.max_damage = max_damage #Should be a MaxDamage object
        self.damage_fraction = damage_fraction #Should be a DamageFractionHazardSeverity object
        self.prefix = None #Should be two caracters long at maximum

        #Other attributes (will be added later)
        #self.damage_fraction - x-values correspond to hazard_intenity; y-values correspond to damage fraction [0-1]
        #self.hazard_intensity_unit #the unit of the x-values

        #self.max_damage / reconstruction costs #length unit and width unit
        #asset type
        #price level etc

    def apply(self,df):
        #This functions needs to be specified in child classes
        logging.warning("""This method has not been applied. """)

    def add_max_dam(self,df):
        #This functions needs to be specified in child classes
        logging.warning("""This method has not been applied. """)

    def set_prefix(self):
        self.prefix = self.name[0:2]
        logging.info("The prefix: '{}' refers to curve name '{}' in the results".format(
            self.prefix,self.name
        ))





class DamageFunction_by_RoadType_by_Lane(DamageFunction):
    """
    A damage function that has different max damages per road type, but a uniform damage_fraction curve


    The attributes need to be of the type:
    self.max_damage (MaxDamage_byRoadType_byLane)
    self.damage_fraction (DamageFractionHazardSeverityUniform)

    """

    def __init__(self, max_damage=None, damage_fraction=None,
                 name=None,hazard='flood',type='depth_damage',infra_type='road'):
        # Construct using the parent class __init__
        DamageFunction.__init__(self, max_damage=max_damage,damage_fraction=damage_fraction,
                                name=name,hazard=hazard,type=type,infra_type=infra_type)
        #Do extra stuffs

    def from_input_folder(self,folder_path):
        """Construct a set of damage functions from csv files located in the folder_path

        Arguments:
            *folder_path* (Pathlib Path) : path to folder where csv files can be found
        """
        #Load the max_damage object
        max_damage = MaxDamage_byRoadType_byLane()
        #search in the folder for something *max_damage*
        #folder_path = Path(r"D:\Python\ra2ce\data\1010b_zuid_holland\input\damage_function\test")
        max_dam_path = find_unique_csv_file(folder_path, "max_damage")
        max_damage.from_csv(max_dam_path, sep=';')

        self.max_damage = max_damage

        #Load the damage fraction function
        #search in the folder for something *damage_fraction
        damage_fraction = DamageFractionUniform()
        dam_fraction_path = find_unique_csv_file(folder_path, "hazard_severity")
        damage_fraction.from_csv(dam_fraction_path, sep=';')
        self.damage_fraction = damage_fraction

        damage_fraction.create_interpolator()


    #Todo: these two below functions are maybe better implemented at a lower level?
    def add_max_damage(self,df,prefix=None):
        """"Ads the max damage value to the dataframe"""
        cols = df.columns
        assert "road_type" in cols, "no column 'road type' in df"
        assert "lanes" in cols, "no column 'lanes in df"

        max_damage_data = self.max_damage.data
        df['{}_temp_max_dam'.format(prefix)] = max_damage_data.lookup(df["road_type"],df["lanes"])
        return df

    def calculate_damage(self,df,DamFun_prefix,hazard_prefix,event_prefix):
        """Calculates the damage for one event

        The prefixes are used to find/set the right df columns

        Arguments:
            *df* (pd.Dataframe) : dataframe with road network data
            *DamFun_prefix* : prefix to identify the right damage function e.g. 'A'
            *hazard_prefix* : prefix to identify the right hazard e.g. 'F'
            *event_prefix*  : prefix to identify the right event, e.g. 'EV1'

        """

        interpolator = self.damage_fraction.interpolator #get the interpolator function

        #Find correct columns in dataframe
        result_col = "dam_{}_{}".format(event_prefix,DamFun_prefix)
        max_dam_col = "{}_temp_max_dam".format(DamFun_prefix)
        hazard_severity_col = "{}_{}_me".format(hazard_prefix,event_prefix) #mean is hardcoded now

        df[result_col] = round(
            df[max_dam_col].astype(float) #max damage (euro/m)
            * interpolator(df[hazard_severity_col].astype(float)) # damage curve  (-)
            * df["length"], #segment length (m),
            0) #round to whole numbers
        return df




def find_unique_csv_file(folder_path,part_of_filename):
    """
    Arguments: find unique csv file in a folder, with a given part_of_filename
    Raises a warning if no file can be found, and an error if more than one file is found

    :param folder_path: (pathlib Path) - The folder in which the csv is searched for
    :return: result (pathlib Path) - The path with the csv file
    """
    result = []
    for file in folder_path.iterdir():
        if (part_of_filename in file.stem) and (file.suffix == '.csv'):
            result.append(file)
    if len(result) > 1:
        raise ValueError("Found more then one damage file in {}".format(folder_path))
    elif len(result) == 0:
        logging.warning("Did not found any damage file in {}".format(folder_path))
    else:
        result = result[0]
    return result





class MaxDamage():
    """
    Base class for data containing maximum damage or construction costs data.

    """
    pass

class MaxDamage_byRoadType_byLane(MaxDamage):
    """
    Subclass of MaxDamage, containing max damage per RoadType and per Lane

    Attributes:
        self.name (str) : Name of the damage curve
        self.data (pd.DataFrame) : columns contain number of lanes; rows contain the road types

    Optional attributes:
        self.origin_path (Path) : Path to the file from which the function was constructed
        self.raw_data : The raw data read from the input file


    """
    def __init__(self,name=None,damage_unit=None):
        self.name = name
        self.damage_unit = damage_unit

    def from_csv(self,path: Path,sep=',',output_unit='euro/m') -> None:
        """Construct object from csv file. Damage curve name is inferred from filename

        The first row describe the lane numbers per column; and should have 'Road_type \ lanes' as index/first value
        The second row has the units per column, and should have 'unit' as index/first value
        the rest of the rows contains the different road types as index/first value; and the costs as values

        Arguments:
            *path* (Path) : Path to the csv file
            *sep* (str) : csv seperator
            *output_unit* (str) : desired output unit (default = 'euro/m')

        """
        self.name = path.stem
        self.raw_data = pd.read_csv(path,index_col='Road_type \ lanes',sep=sep)
        self.origin_path = path #to track the original path from which the object was constructed; maybe also date?

        ###Determine units
        units = self.raw_data.loc['unit',:].unique() #identify the unique units
        assert len(units) == 1, 'Columns in the max damage csv seem to have different units, ra2ce cannot handle this'
        #case only one unique unit is identified
        self.damage_unit = units[0] #should have the structure 'x/y' , e.g. euro/m, dollar/yard

        self.data = self.raw_data.drop('unit')
        self.data = self.data.astype('float')

        #assume road types are in the rows; lane numbers in the columns
        self.road_types = list(self.data.index) #to method
        #assumes that the columns containst the lanes
        self.data.columns = self.data.columns.astype('int')


        if self.damage_unit != 'output_unit':
            self.convert_length_unit() #convert the unit


    def convert_length_unit(self,desired_unit='euro/m') -> None:
        """Converts max damage values to a different unit
        Arguments:
            self.damage_unit (implicit)
            *desired_unit* (string)

        Effect: converts the values in self.data; and sets the new damage_unit

        Returns: the factor by which the original unit has been scaled

        """
        if desired_unit == self.damage_unit:
            logging.info('Input damage units are already in the desired format')
            return None

        original_length_unit = self.damage_unit.split('/')[1]
        target_length_unit = desired_unit.split('/')[1]

        if (original_length_unit == 'km' and target_length_unit == 'm'):
            scaling_factor = 1/1000
            self.data = self.data * scaling_factor
            logging.info('Damage data from {} was scaled by a factor {}, to convert from {} to {}'.format(
                self.origin_path, scaling_factor,self.damage_unit,desired_unit))
            self.damage_unit = desired_unit
            return None
        else:
            logging.warning('Damage scaling from {} to {} is not supported'.format(self.damage_unit,desired_unit))
            return None

class DamageFraction():
    """
    Base class for data containing maximum damage or construction costs data.

    """
    pass

class DamageFractionUniform(DamageFraction):
    """
    Uniform: assuming the same curve for
    each road type and lane numbers and any other metadata


    self.raw_data (pd.DataFrame) : Raw data from the csv file
    self.data (pd.DataFrame) : index = hazard severity (e.g. flood depth); column 0 = damage fraction

    """
    def __init__(self,name=None,hazard_unit=None):
        self.name = name
        self.hazard_unit = hazard_unit
        self.interpolator = None

    def from_csv(self,path: Path,sep=',',desired_unit='m') -> None:
        """Construct object from csv file. Damage curve name is inferred from filename

        Arguments:
            *path* (Path) : Path to the csv file
            *sep* (str) : csv seperator
            *output_unit* (str) : desired output unit (default = 'm')

        The CSV file should have the following structure:
         - column 1: hazard severity
         - column 2: damage fraction
         - row 1: column names
         - row 2: unit of column:

        Example:
                +- ------+-------------------------------+
                | depth | damage                        |
                +-------+-------------------------------+
                | cm    | % of total construction costs |
                +-------+-------------------------------+
                | 0     | 0                             |
                +-------+-------------------------------+
                | 50    | 0.25                          |
                +-------+-------------------------------+
                | 100   | 0.42                          |
                +-------+-------------------------------+


        """
        self.name = path.stem
        self.raw_data = pd.read_csv(path,index_col=0,sep=sep)
        self.origin_path = path #to track the original path from which the object was constructed; maybe also date?

        #identify unit and drop from data
        self.hazard_unit = self.raw_data.index[0]
        self.data = self.raw_data.drop(self.hazard_unit) #Todo: This could also be a series instead of DataFrame

        #convert data to floats
        self.data = self.data.astype('float')
        self.data.index = self.data.index.astype('float')

        self.convert_hazard_severity_unit()

    def convert_hazard_severity_unit(self,desired_unit='m') -> None:
        """Converts hazard severity values to a different unit
        Arguments:
            self.hazard_unit - implicit (string)
            *desired_unit* (string)

        Effect: converts the values in self.data; and sets the new damage_unit to the desired unit

        """
        if desired_unit == self.hazard_unit:
            logging.info('Damage units are already in the desired format {}'.format(desired_unit))
            return None

        if (self.hazard_unit == 'cm' and desired_unit == 'm'):
            scaling_factor = 1/100
            self.data.index = self.data.index * scaling_factor
            logging.info('Hazard severity from {} data was scaled by a factor {}, to convert from {} to {}'.format(
                self.origin_path, scaling_factor,self.hazard_unit,desired_unit))
            self.damage_unit = desired_unit
            return None
        else:
            logging.warning('Hazard severity scaling from {} to {} is not  supported'.format(self.hazard_unit,desired_unit))
            return None

    def create_interpolator(self):
        """ Create interpolator object from loaded data
        sets result to self.interpolator (Scipy interp1d)
        """
        from scipy.interpolate import interp1d
        x_values = self.data.index.values
        y_values = self.data.values[:,0]

        self.interpolator = interp1d(x=x_values,y=y_values,
                fill_value=(y_values[0],y_values[-1]), #fraction damage (y) if hazard severity (x) is outside curve range
                bounds_error=False)

        return None

    def __repr__(self):
        if self.interpolator:
            string = 'DamageFractionUniform with name: ' + self.name + ' interpolator: {}'.format(
                list(zip(self.interpolator.y, self.interpolator.x)))
        else:
            string = 'DamageFractionUniform with name: ' +  self.name
        return string