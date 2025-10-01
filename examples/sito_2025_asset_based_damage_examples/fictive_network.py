from pathlib import Path

from ra2ce.ra2ce_handler import Ra2ceHandler
from ra2ce.analysis.damages.damages import AnalysisSectionDamages
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import AnalysisDamagesEnum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import RiskCalculationModeEnum

root_dir = Path("fictive_network")


assert root_dir.exists(), "root_dir not found."

static_path = root_dir.joinpath("static")
hazard_path =root_dir.joinpath("hazard")
polygon_path = static_path.joinpath("static")
output_path=root_dir.joinpath("output")

hazard_map = list(hazard_path.glob("*.tif"))



# specify the parameters for the damage analysis
damages_analysis = [AnalysisSectionDamages(
    name='damages_with_asset',
    analysis=AnalysisDamagesEnum.DAMAGES_WITH_ASSETS,
    event_type=EventTypeEnum.RETURN_PERIOD,
    damage_curve=DamageCurveEnum.MAN,
    risk_calculation_mode=RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR,
    risk_calculation_year=5,
    save_csv=True,
    save_gpkg=True
)]

analysis_config_data = AnalysisConfigData(
    analyses=damages_analysis,
    root_path=root_dir,
    input_path=Path.cwd().joinpath("input_data"),
    output_path=output_path,
)

analysis_config_data.input_path = root_dir.joinpath("input_data")

handler = Ra2ceHandler.from_config(None, analysis_config_data)
handler.input_config.analysis_config.graph_files.base_graph_hazard.folder = static_path.joinpath("output_graph")
handler.input_config.analysis_config.graph_files.base_network_hazard.folder = static_path.joinpath("output_graph")

handler.configure()
handler.run_analysis()