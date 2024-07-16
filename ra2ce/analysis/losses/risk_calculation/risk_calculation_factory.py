import geopandas as gpd
from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)


class RiskCalculationFactory:
    @staticmethod
    def get_risk_calculation(
        risk_calculation_mode: RiskCalculationModeEnum,
        risk_calculation_year: int,
        losses_gdf: gpd.GeoDataFrame,
    ):
        if risk_calculation_mode == RiskCalculationModeEnum.DEFAULT:
            pass
        if risk_calculation_mode == RiskCalculationModeEnum.CUT_FROM_YEAR:
            pass
        if risk_calculation_mode == RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR:
            pass
        raise NotImplementedError(
            "Risk calculation mode {} not yet supported.".format(risk_calculation_mode)
        )
