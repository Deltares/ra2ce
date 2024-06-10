import math

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
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


class WeighingAnalysisFactory:
    @staticmethod
    def get_analysis(
        weighing_type: WeighingEnum, gdf_graph: gpd.GeoDataFrame
    ) -> WeighingAnalysisProtocol:
        def _get_avgspeed_for_roadtype(
            gdf_graph: gpd.GeoDataFrame, road_type: RoadTypeEnum
        ) -> float:
            # get the average speed for the road type
            _avgspeed = gdf_graph[gdf_graph["highway"] == road_type.config_value][
                "avgspeed"
            ]
            _avg = _avgspeed[_avgspeed > 0].mean()
            if not _avg or math.isnan(_avg):
                # if the average speed is not available,
                # get the average speed of the whole graph
                _avgspeed = gdf_graph["avgspeed"]
                return _avgspeed[_avgspeed > 0].mean()
            return _avg

        if weighing_type == WeighingEnum.TIME:
            _analysis = TimeWeighingAnalysis()
        elif weighing_type == WeighingEnum.LENGTH:
            _analysis = LengthWeighingAnalysis()
        else:
            raise NotImplementedError(
                "Weighing type {} not yet supported.".format(weighing_type)
            )

        _analysis.avgspeed_dict = {
            _road_type.config_value: _get_avgspeed_for_roadtype(gdf_graph, _road_type)
            for _road_type in RoadTypeEnum
        }

        return _analysis
