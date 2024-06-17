import geopandas as gpd

from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.losses.weighing_analysis.length_weighing_analysis import (
    LengthWeighingAnalysis,
)
from ra2ce.analysis.losses.weighing_analysis.time_weighing_analysis import (
    TimeWeighingAnalysis,
)
from ra2ce.analysis.losses.weighing_analysis.weighing_analysis_protocol import (
    WeighingAnalysisProtocol,
)


class WeighingAnalysisFactory:
    @staticmethod
    def get_analysis(
        weighing_type: WeighingEnum, gdf_graph: gpd.GeoDataFrame | None
    ) -> WeighingAnalysisProtocol:
        if weighing_type == WeighingEnum.TIME:
            return TimeWeighingAnalysis(gdf_graph)
        if weighing_type == WeighingEnum.LENGTH:
            return LengthWeighingAnalysis(gdf_graph)

        raise NotImplementedError(
            "Weighing type {} not yet supported.".format(weighing_type)
        )
