from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class AnalysisDamagesEnum(Ra2ceEnumBase):
    DAMAGES = 1
    EFFECTIVENESS_MEASURES = 2
    ADAPTATION = 3
    INVALID = 99

    # TODO: remove after refactoring the enum to AnalysisEnum
    @classmethod
    def list_valid_options(cls):
        return [
            cls.DAMAGES,
            cls.EFFECTIVENESS_MEASURES,
        ]
