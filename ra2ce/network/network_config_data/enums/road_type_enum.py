from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class RoadTypeEnum(Ra2ceEnumBase):
    """
    Enumeration of OpenStreetMap (OSM) road types.

    This enum provides integer identifiers for road types as defined by
    OpenStreetMap (OSM) tagging conventions. These types are commonly
    used in routing, navigation, and map rendering.

    Attributes
    ----------
    NONE : int
        No road type (0).
    MOTORWAY : int
        OSM ``highway=motorway`` — major highway, usually with controlled access (1).
    MOTORWAY_LINK : int
        OSM ``highway=motorway_link`` — link roads (on/off ramps) connecting to a motorway (2).
    TRUNK : int
        OSM ``highway=trunk`` — important roads, typically linking cities or regions (3).
    TRUNK_LINK : int
        OSM ``highway=trunk_link`` — link roads connecting to a trunk road (4).
    PRIMARY : int
        OSM ``highway=primary`` — major roads between towns or districts (5).
    PRIMARY_LINK : int
        OSM ``highway=primary_link`` — link roads connecting to a primary road (6).
    SECONDARY : int
        OSM ``highway=secondary`` — roads connecting smaller towns and settlements (7).
    SECONDARY_LINK : int
        OSM ``highway=secondary_link`` — link roads connecting to a secondary road (8).
    TERTIARY : int
        OSM ``highway=tertiary`` — local connector roads within regions (9).
    TERTIARY_LINK : int
        OSM ``highway=tertiary_link`` — link roads connecting to a tertiary road (10).
    RESIDENTIAL : int
        OSM ``highway=residential`` — roads serving residential areas (11).
    ROAD : int
        OSM ``highway=road`` — generic, unclassified road type (12).
    TUNNEL : int
        OSM ``tunnel=yes`` — road passing underground (13).
    BRIDGE : int
        OSM ``bridge=yes`` — road passing over an obstacle (14).
    CULVERT : int
        OSM ``culvert=yes`` — small passage under a road, often for water flow (15).
    RAIL : int
        OSM ``railway=*`` — railway tracks (16).
    UNCLASSIFIED : int
        OSM ``highway=unclassified`` — minor public road, less important than tertiary (98).
    INVALID : int
        Invalid or unsupported OSM road type (99).

    Notes
    -----
    These identifiers are based on OSM tagging conventions.
    See: https://wiki.openstreetmap.org/wiki/Key:highway
    """
    NONE = 0
    MOTORWAY = 1
    MOTORWAY_LINK = 2
    TRUNK = 3
    TRUNK_LINK = 4
    PRIMARY = 5
    PRIMARY_LINK = 6
    SECONDARY = 7
    SECONDARY_LINK = 8
    TERTIARY = 9
    TERTIARY_LINK = 10
    RESIDENTIAL = 11
    ROAD = 12
    TUNNEL = 13
    BRIDGE = 14
    CULVERT = 15
    RAIL = 16
    UNCLASSIFIED = 98
    INVALID = 99

    @classmethod
    def get_enum(cls, input: str | None) -> Ra2ceEnumBase:
        return super().get_enum(input)
