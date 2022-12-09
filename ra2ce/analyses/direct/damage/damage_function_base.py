import logging


class DamageFunctionBase:
    """
    Generic damage function
    CS: No real reason to have this as a single class when it's only being inherited (and instanced) by `damage_unction_road_type_lane.py`.
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
        self.name = name
        self.hazard = hazard
        self.type = type
        self.infra_type = infra_type
        self.max_damage = max_damage  # Should be a MaxDamage object
        self.damage_fraction = (
            damage_fraction  # Should be a DamageFractionHazardSeverity object
        )
        self.prefix = None  # Should be two characters long at maximum

        # Other attributes (will be added later)
        # self.damage_fraction - x-values correspond to hazard_intenity; y-values correspond to damage fraction [0-1]
        # self.hazard_intensity_unit #the unit of the x-values

        # self.max_damage / reconstruction costs #length unit and width unit
        # asset type
        # price level etc

    def from_input_folder(self, df):
        # This functions needs to be specified in child classes
        logging.warning("""This method has not been specified in the parent class. """)

    def add_max_dam(self, df):
        # This functions needs to be specified in child classes
        logging.warning("""This method has not been applied. """)

    def set_prefix(self):
        self.prefix = self.name[0:2]
        logging.info(
            "The prefix: '{}' refers to curve name '{}' in the results".format(
                self.prefix, self.name
            )
        )
