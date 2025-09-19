from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class RiskCalculationModeEnum(Ra2ceEnumBase):
    """
    Enumeration of risk calculation modes.

    This enum defines strategies for computing risk from damage curves
    and event probabilities. The modes differ in how they treat return
    periods (RPs) outside of the known range and whether cutoff years
    are applied.


    .. image:: /_resources/default.png
       :alt: Risk calculation modes
       :align: center
       :scale: 50%


    .. image:: /_resources/cut_from_year.png
       :alt: Risk calculation modes
       :align: center
       :scale: 50%


    .. image:: /_resources/triangle_to_null.png
       :alt: Risk calculation modes
       :align: center
       :scale: 50%

    Attributes
    ----------
    NONE : int
        No risk calculation mode specified (0).
    DEFAULT : int
        Standard or default risk calculation mode (1).
    CUT_FROM_YEAR : int
        Cut-from mode (2).

        - For all RPs larger than the largest known RP, assume that
          the damage equals the damage of the largest known RP.
        - No risk for all events with a return period smaller than
          the smallest known RP.
        - All damage caused by events with RP > ``risk_calculation_year``
          does not contribute to risk.
    TRIANGLE_TO_NULL_YEAR : int
        Triangle-to-null mode (3).

        - For all RPs larger than the largest known RP, assume that
          the damage equals the damage of the largest known RP.
        - From the lowest return period, draw a triangle to a certain
          value (given by ``risk_calculation_year``), and add the area
          of this triangle to the risk.
    INVALID : int
        Invalid or unsupported risk calculation mode (99).
    """
    NONE = 0
    DEFAULT = 1
    CUT_FROM_YEAR = 2
    TRIANGLE_TO_NULL_YEAR = 3
    INVALID = 99
