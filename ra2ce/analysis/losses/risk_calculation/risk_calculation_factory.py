import geopandas as gpd

from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)
from ra2ce.analysis.losses.risk_calculation.risk_calculation_cut_from_year import (
    RiskCalculationCutFromYear,
)
from ra2ce.analysis.losses.risk_calculation.risk_calculation_default import (
    RiskCalculationDefault,
)
from ra2ce.analysis.losses.risk_calculation.risk_calculation_triangle_to_null_year import (
    RiskCalculationTriangleToNullYear,
)


class RiskCalculationFactory:
    @staticmethod
    def get_risk_calculation(
        risk_calculation_mode: RiskCalculationModeEnum,
        risk_calculation_year: int,
        losses_gdf: gpd.GeoDataFrame,
    ):
        if risk_calculation_mode == RiskCalculationModeEnum.DEFAULT:
            return RiskCalculationDefault(risk_calculation_year, losses_gdf)
        if risk_calculation_mode == RiskCalculationModeEnum.CUT_FROM_YEAR:
            return RiskCalculationCutFromYear(risk_calculation_year, losses_gdf)
        if risk_calculation_mode == RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR:
            return RiskCalculationTriangleToNullYear(risk_calculation_year, losses_gdf)
        raise NotImplementedError(
            "Risk calculation mode {} not yet supported.".format(risk_calculation_mode)
        )
