"""
                    GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

    Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023 Stichting Deltares

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from configparser import ConfigParser
from pathlib import Path

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionAdaptation,
    AnalysisSectionAdaptationOption,
    AnalysisSectionDamages,
    AnalysisSectionLosses,
    DamagesAnalysisNameList,
    LossesAnalysisNameList,
    ProjectSection,
)
from ra2ce.analysis.analysis_config_data.analysis_config_data_protocol import (
    AnalysisConfigDataProtocol,
)
from ra2ce.analysis.analysis_config_data.base_link_losses_config_data import (
    BaseLinkLossesConfigData,
    MultiLinkLossesConfigData,
    SingleLinkLossesConfigData,
)
from ra2ce.analysis.analysis_config_data.base_origin_destination_config_data import (
    BaseOriginDestinationConfigData,
    MultiLinkOriginClosestDestinationConfigData,
    MultiLinkOriginDestinationConfigData,
    OptimalRouteOriginClosestDestinationConfigData,
    OptimalRouteOriginDestinationConfigData,
)
from ra2ce.analysis.analysis_config_data.damages_config_data import DamagesConfigData
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_enum import AnalysisEnum
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)
from ra2ce.analysis.analysis_config_data.enums.traffic_period_enum import (
    TrafficPeriodEnum,
)
from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.analysis_config_data.multi_link_redundancy_config_data import (
    MultiLinkRedundancyConfigData,
)
from ra2ce.analysis.analysis_config_data.single_link_redundancy_config_data import (
    SingleLinkRedundancyConfigData,
)
from ra2ce.common.configuration.ini_configuration_reader_protocol import (
    ConfigDataReaderProtocol,
)


class AnalysisConfigDataReader(ConfigDataReaderProtocol):
    """
    Reads the analysis configuration file analyses.ini.
    """

    _parser: ConfigParser

    def __init__(self) -> None:
        self._parser = ConfigParser(
            inline_comment_prefixes="#",
            converters={"list": lambda x: [x.strip() for x in x.split(",")]},
        )

    def read(self, ini_file: Path) -> AnalysisConfigData:
        if not isinstance(ini_file, Path) or not ini_file.is_file():
            raise ValueError("No analysis ini file 'Path' provided.")
        self._parser.read(ini_file)
        self._remove_none_values()

        _parent_dir = ini_file.parent
        _config_data = AnalysisConfigData(
            root_path=_parent_dir.parent,
            input_path=_parent_dir.joinpath("input"),
            static_path=_parent_dir.joinpath("static"),
            output_path=_parent_dir.joinpath("output"),
            **self._get_sections(),
        )
        _config_data.project.name = _parent_dir.name

        return _config_data

    def _remove_none_values(self) -> None:
        # Remove 'None' from values, replace them with empty strings
        for _section in self._parser.sections():
            _keys_with_none = [
                k for k, v in self._parser[_section].items() if v == "None"
            ]
            for _key_with_none in _keys_with_none:
                self._parser[_section].pop(_key_with_none)

    def _get_sections(self) -> dict:
        return {
            "project": self.get_project_section(),
            "analyses": self.get_analysis_sections(),
        }

    def get_project_section(self) -> ProjectSection:
        return ProjectSection(**self._parser["project"])

    def _set_section_common_properties(
        self, section: AnalysisConfigDataProtocol, section_name: str
    ) -> None:
        section.name = self._parser.get(section_name, "name", fallback=section.name)
        section.save_gpkg = self._parser.getboolean(
            section_name, "save_gpkg", fallback=section.save_gpkg
        )
        section.save_csv = self._parser.getboolean(
            section_name, "save_csv", fallback=section.save_csv
        )

    def _get_single_link_redundancy_config_data(
        self, section_name: str
    ) -> SingleLinkRedundancyConfigData:
        _section = SingleLinkRedundancyConfigData.from_ini_file(
            **self._parser[section_name]
        )
        self._set_section_common_properties(_section, section_name)

        _section.weighing = WeighingEnum.get_enum(
            self._parser.get(section_name, "weighing", fallback=None)
        )
        return _section

    def _get_multi_link_redundancy_config_data(
        self, section_name: str
    ) -> MultiLinkRedundancyConfigData:
        _section = MultiLinkRedundancyConfigData.from_ini_file(
            **self._parser[section_name]
        )
        self._set_section_common_properties(_section, section_name)

        _section.calculate_route_without_disruption = self._parser.getboolean(
            section_name,
            "calculate_route_without_disruption",
            fallback=_section.calculate_route_without_disruption,
        )
        _section.threshold = self._parser.getfloat(
            section_name,
            "threshold",
            fallback=_section.threshold,
        )
        _section.threshold_destinations = self._parser.getfloat(
            section_name,
            "threshold_destinations",
            fallback=_section.threshold_destinations,
        )
        _section.buffer_meters = self._parser.getfloat(
            section_name,
            "buffer_meters",
            fallback=_section.buffer_meters,
        )
        return _section

    def _get_damages_config_data(self, section_name: str) -> DamagesConfigData:
        _section = DamagesConfigData.from_ini_file(**self._parser[section_name])
        self._set_section_common_properties(_section, section_name)

        # road damage
        _section.event_type = EventTypeEnum.get_enum(
            self._parser.get(section_name, "event_type", fallback=None)
        )
        _section.risk_calculation_mode = RiskCalculationModeEnum.get_enum(
            self._parser.get(section_name, "risk_calculation_mode", fallback=None)
        )
        _section.risk_calculation_year = self._parser.getint(
            section_name,
            "risk_calculation_year",
            fallback=_section.risk_calculation_year,
        )
        _section.damage_curve = DamageCurveEnum.get_enum(
            self._parser.get(section_name, "damage_curve", fallback=None)
        )
        _section.create_table = self._parser.getboolean(
            section_name,
            "create_table",
            fallback=_section.create_table,
        )
        return _section

    def _get_base_link_losses_config_data(
        self, section_name: str, config_data_type: type[BaseLinkLossesConfigData]
    ) -> AnalysisConfigDataProtocol:
        _section = config_data_type.from_ini_file(**self._parser[section_name])
        self._set_section_common_properties(_section, section_name)

        _section.event_type = EventTypeEnum.get_enum(
            self._parser.get(section_name, "event_type", fallback=None)
        )
        _section.weighing = WeighingEnum.get_enum(
            self._parser.get(section_name, "weighing", fallback=None)
        )
        _section.production_loss_per_capita_per_hour = self._parser.getfloat(
            section_name,
            "production_loss_per_capita_per_hour",
            fallback=_section.production_loss_per_capita_per_hour,
        )
        _section.traffic_period = TrafficPeriodEnum.get_enum(
            self._parser.get(section_name, "traffic_period", fallback=None)
        )
        _section.trip_purposes = list(
            map(
                TripPurposeEnum.get_enum,
                self._parser.getlist(section_name, "trip_purposes", fallback=[]),
            )
        )
        _section.resilience_curves_file = self._parser.get(
            section_name,
            "resilience_curves_file",
            fallback=_section.resilience_curves_file,
        )
        _section.traffic_intensities_file = self._parser.get(
            section_name,
            "traffic_intensities_file",
            fallback=_section.traffic_intensities_file,
        )
        _section.values_of_time_file = self._parser.get(
            section_name,
            "values_of_time_file",
            fallback=_section.values_of_time_file,
        )
        _section.risk_calculation_mode = RiskCalculationModeEnum.get_enum(
            self._parser.get(section_name, "risk_calculation_mode", fallback=None)
        )
        _section.risk_calculation_year = self._parser.getint(
            section_name,
            "risk_calculation_year",
            fallback=_section.risk_calculation_year,
        )
        return _section

    def _get_origin_destination_config_data(
        self, section_name: str, config_data_type: type[BaseOriginDestinationConfigData]
    ) -> AnalysisConfigDataProtocol:
        _section = config_data_type.from_ini_file(**self._parser[section_name])
        self._set_section_common_properties(_section, section_name)
        _section.weighing = WeighingEnum.get_enum(
            self._parser.get(section_name, "weighing", fallback=None)
        )
        _section.calculate_route_without_disruption = self._parser.getboolean(
            section_name,
            "calculate_route_without_disruption",
            fallback=_section.calculate_route_without_disruption,
        )
        _section.threshold = self._parser.getfloat(
            section_name,
            "threshold",
            fallback=_section.threshold,
        )
        _section.threshold_destinations = self._parser.getfloat(
            section_name,
            "threshold_destinations",
            fallback=_section.threshold_destinations,
        )
        _section.buffer_meters = self._parser.getfloat(
            section_name,
            "buffer_meters",
            fallback=_section.buffer_meters,
        )
        return _section

    def _get_analysis_sections_with_new_dataclasses(
        self,
    ) -> list[AnalysisConfigDataProtocol]:
        """
        Extracts info from [analysis<n>] sections

        Returns:
            list[AnalysisConfigDataProtocol]: List of analyses
        """
        _mappers = {
            AnalysisLossesEnum.SINGLE_LINK_REDUNDANCY.config_value: self._get_single_link_redundancy_config_data,
            AnalysisLossesEnum.MULTI_LINK_REDUNDANCY.config_value: self._get_multi_link_redundancy_config_data,
            AnalysisLossesEnum.SINGLE_LINK_LOSSES.config_value: lambda x: self._get_base_link_losses_config_data(
                x, SingleLinkLossesConfigData
            ),
            AnalysisLossesEnum.MULTI_LINK_LOSSES.config_value: lambda x: self._get_base_link_losses_config_data(
                x, MultiLinkLossesConfigData
            ),
            AnalysisLossesEnum.OPTIMAL_ROUTE_ORIGIN_DESTINATION.config_value: lambda x: self._get_origin_destination_config_data(
                x, OptimalRouteOriginDestinationConfigData
            ),
            AnalysisLossesEnum.OPTIMAL_ROUTE_ORIGIN_CLOSEST_DESTINATION.config_value: lambda x: self._get_origin_destination_config_data(
                x, OptimalRouteOriginClosestDestinationConfigData
            ),
            AnalysisLossesEnum.MULTI_LINK_ORIGIN_DESTINATION.config_value: lambda x: self._get_origin_destination_config_data(
                x, MultiLinkOriginDestinationConfigData
            ),
            AnalysisLossesEnum.MULTI_LINK_ORIGIN_CLOSEST_DESTINATION.config_value: lambda x: self._get_origin_destination_config_data(
                x, MultiLinkOriginClosestDestinationConfigData
            ),
            AnalysisDamagesEnum.DAMAGES.config_value: self._get_damages_config_data,
        }

        def raise_not_supported(analysis_type_name: str):
            raise ValueError(f"Analysis {analysis_type_name} not supported.")

        def get_mapping_function(section_name: str) -> AnalysisConfigDataProtocol:
            _analysis_type = self._parser.get(section_name, "analysis", fallback=None)
            _mapping_function = _mappers.get(_analysis_type, raise_not_supported)
            return _mapping_function(section_name)

        return list(
            get_mapping_function(section_name)
            for section_name in self._parser.sections()
            if "analysis" in section_name
        )

    def _get_analysis_section_losses(self, section_name: str) -> AnalysisSectionLosses:
        _section = AnalysisSectionLosses(**self._parser[section_name])
        _section.analysis = AnalysisLossesEnum.get_enum(
            self._parser.get(section_name, "analysis", fallback=None)
        )
        _section.save_gpkg = self._parser.getboolean(
            section_name, "save_gpkg", fallback=_section.save_gpkg
        )
        _section.save_csv = self._parser.getboolean(
            section_name, "save_csv", fallback=_section.save_csv
        )
        _weighing = self._parser.get(section_name, "weighing", fallback=None)
        # Map distance -> length
        if _weighing == "distance":
            _section.weighing = WeighingEnum.LENGTH
        else:
            _section.weighing = WeighingEnum.get_enum(_weighing)

        # losses
        _section.event_type = EventTypeEnum.get_enum(
            self._parser.get(section_name, "event_type", fallback=None)
        )
        _section.risk_calculation_mode = RiskCalculationModeEnum.get_enum(
            self._parser.get(section_name, "risk_calculation_mode", fallback=None)
        )
        _section.risk_calculation_year = self._parser.getint(
            section_name,
            "risk_calculation_year",
            fallback=_section.risk_calculation_year,
        )
        _section.traffic_period = TrafficPeriodEnum.get_enum(
            self._parser.get(section_name, "traffic_period", fallback=None)
        )
        _section.hours_per_traffic_period = self._parser.getint(
            section_name,
            "hours_per_traffic_period",
            fallback=_section.hours_per_traffic_period,
        )
        _section.trip_purposes = list(
            map(
                TripPurposeEnum.get_enum,
                self._parser.getlist(section_name, "trip_purposes", fallback=[]),
            )
        )
        _section.production_loss_per_capita_per_hour = self._parser.getfloat(
            section_name,
            "production_loss_per_capita_per_hour",
            fallback=_section.production_loss_per_capita_per_hour,
        )

        # accessibility analyses
        _section.threshold = self._parser.getfloat(
            section_name,
            "threshold",
            fallback=_section.threshold,
        )
        _section.threshold_destinations = self._parser.getfloat(
            section_name,
            "threshold_destinations",
            fallback=_section.threshold_destinations,
        )
        _section.calculate_route_without_disruption = self._parser.getboolean(
            section_name,
            "calculate_route_without_disruption",
            fallback=_section.calculate_route_without_disruption,
        )
        _section.buffer_meters = self._parser.getfloat(
            section_name,
            "buffer_meters",
            fallback=_section.buffer_meters,
        )
        _section.save_traffic = self._parser.getboolean(
            section_name, "save_traffic", fallback=_section.save_traffic
        )

        return _section

    def _get_analysis_section_damages(
        self, section_name: str
    ) -> AnalysisSectionDamages:
        _section = AnalysisSectionDamages(**self._parser[section_name])
        _section.analysis = AnalysisDamagesEnum.get_enum(
            self._parser.get(section_name, "analysis", fallback=None)
        )
        _section.save_gpkg = self._parser.getboolean(
            section_name, "save_gpkg", fallback=_section.save_gpkg
        )
        _section.save_csv = self._parser.getboolean(
            section_name, "save_csv", fallback=_section.save_csv
        )

        # road damage
        _section.event_type = EventTypeEnum.get_enum(
            self._parser.get(section_name, "event_type", fallback=None)
        )
        _section.risk_calculation_mode = RiskCalculationModeEnum.get_enum(
            self._parser.get(section_name, "risk_calculation_mode", fallback=None)
        )
        _section.risk_calculation_year = self._parser.getint(
            section_name,
            "risk_calculation_year",
            fallback=_section.risk_calculation_year,
        )
        _section.damage_curve = DamageCurveEnum.get_enum(
            self._parser.get(section_name, "damage_curve", fallback=None)
        )
        _section.create_table = self._parser.getboolean(
            section_name,
            "create_table",
            fallback=_section.create_table,
        )
        return _section

    def _get_analysis_section_adaptation(
        self, section_name: str
    ) -> AnalysisSectionAdaptation:
        def _get_adaptation_option(
            section_name: str,
        ) -> AnalysisSectionAdaptationOption:
            return AnalysisSectionAdaptationOption(**self._parser[section_name])

        _section = AnalysisSectionAdaptation(**self._parser[section_name])
        _section.analysis = AnalysisEnum.get_enum(
            self._parser.get(section_name, "analysis", fallback=None)
        )
        _section.losses_analysis = AnalysisLossesEnum.get_enum(
            self._parser.get(section_name, "losses_analysis", fallback=None)
        )
        _section.save_gpkg = self._parser.getboolean(
            section_name, "save_gpkg", fallback=_section.save_gpkg
        )
        _section.save_csv = self._parser.getboolean(
            section_name, "save_csv", fallback=_section.save_csv
        )
        _section.hazard_fraction_cost = self._parser.getboolean(
            section_name,
            "hazard_fraction_costs",
            fallback=_section.hazard_fraction_cost,
        )

        _adaptation_options = list(
            _adaptation_option
            for _adaptation_option in self._parser.sections()
            if "adaptationoption" in _adaptation_option
        )
        for _adaptation_option in _adaptation_options:
            _section.adaptation_options.append(
                _get_adaptation_option(_adaptation_option)
            )

        return _section

    def get_analysis_sections(self) -> list[AnalysisConfigData.ANALYSIS_SECTION]:
        """
        Extracts info from [analysis<n>] sections

        Returns:
            list[ANALYSIS_SECTION]: List of analyses
        """
        _analysis_sections: list[AnalysisConfigData.ANALYSIS_SECTION] = []

        _section_names = list(
            section_name
            for section_name in self._parser.sections()
            if "analysis" in section_name
        )
        for _section_name in _section_names:
            _analysis_type = self._parser.get(_section_name, "analysis")
            if _analysis_type in DamagesAnalysisNameList:
                _analysis_section = self._get_analysis_section_damages(_section_name)
            elif _analysis_type in LossesAnalysisNameList:
                _analysis_section = self._get_analysis_section_losses(_section_name)
            elif _analysis_type == AnalysisEnum.ADAPTATION.config_value:
                _analysis_section = self._get_analysis_section_adaptation(_section_name)
            else:
                raise ValueError(f"Analysis {_analysis_type} not supported.")
            _analysis_sections.append(_analysis_section)

        return _analysis_sections
