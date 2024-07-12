import geopandas as gpd

from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.damages.shape_to_integrate_object.hz_to_integrate_shaper import (
    HzToIntegrateShaper,
)
from ra2ce.analysis.damages.shape_to_integrate_object.man_to_integrate_shaper import (
    ManToIntegrateShaper,
)
from ra2ce.analysis.damages.shape_to_integrate_object.osd_to_integrate_shaper import (
    OsdToIntegrateShaper,
)
from ra2ce.analysis.damages.shape_to_integrate_object.to_Integrate_shaper_protocol import (
    ToIntegrateShaperProtocol,
)


class ToIntegrateShaperFactory:
    @staticmethod
    def get_shaper(
        gdf: gpd.GeoDataFrame, damage_function: DamageCurveEnum
    ) -> ToIntegrateShaperProtocol:
        if damage_function == DamageCurveEnum.HZ:
            return HzToIntegrateShaper(gdf)
        if damage_function == DamageCurveEnum.OSD:
            return OsdToIntegrateShaper(gdf)
        if damage_function == DamageCurveEnum.MAN:
            return ManToIntegrateShaper(gdf)

        raise NotImplementedError(
            f"damage function {damage_function} not yet supported."
        )
