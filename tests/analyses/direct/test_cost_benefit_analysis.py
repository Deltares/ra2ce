import numpy as np
import pandas as pd
import pytest

from ra2ce.analyses.direct.cost_benefit_analysis import EffectivenessMeasures
from tests import test_data


class MockEffectivenessMeasures(EffectivenessMeasures):
    def __init__(self, config, analysis):
        """
        This class is only meant to inherit from `Effectiveness measures` and allow the partial testing of certain methods for pure code coverage reasons.
        """
        pass


class TestCostBenefitAnalysis:
    def test_init_raises_when_file_name_not_defined(self):
        _config = {"input": test_data}
        _analysis = {
            "return_period": None,
            "repair_costs": None,
            "evaluation_period": None,
            "interest_rate": 42,
            "climate_factor": 24,
            "climate_period": 2.4,
            "file_name": None,
        }
        with pytest.raises(ValueError) as exc_err:
            EffectivenessMeasures(_config, _analysis)
        assert (
            str(exc_err.value)
            == "Effectiveness of measures calculation: No input file configured. Please define an input file in the analysis.ini file."
        )

    def test_init_raises_when_file_name_not_shp(self):
        _config = {"input": test_data}
        _analysis = {
            "return_period": None,
            "repair_costs": None,
            "evaluation_period": None,
            "interest_rate": 42,
            "climate_factor": 24,
            "climate_period": 2.4,
            "file_name": "just_a_file.txt",
        }
        with pytest.raises(ValueError) as exc_err:
            EffectivenessMeasures(_config, _analysis)
        assert (
            str(exc_err.value)
            == "Effectiveness of measures calculation: Wrong input file configured. Extension of input file is -txt-, needs to be -shp- (shapefile)"
        )

    def test_init_raises_when_direct_shp_file_does_not_exist(self):
        _config = {"input": test_data}
        _analysis = {
            "return_period": None,
            "repair_costs": None,
            "evaluation_period": None,
            "interest_rate": 42,
            "climate_factor": 24,
            "climate_period": 2.4,
            "file_name": "filedoesnotexist.shp",
        }
        with pytest.raises(FileNotFoundError) as exc_err:
            EffectivenessMeasures(_config, _analysis)
        assert str(exc_err.value) == str(
            _config["input"] / "direct" / "filedoesnotexist.shp"
        )

    def test_init_raises_when_effectiveness_measures_does_not_exist(self):
        _config = {"input": test_data}
        _analysis = {
            "return_period": None,
            "repair_costs": None,
            "evaluation_period": None,
            "interest_rate": 42,
            "climate_factor": 24,
            "climate_period": 2.4,
            "file_name": "origins.shp",
        }
        assert (_config["input"] / "direct" / "origins.shp").exists()
        with pytest.raises(FileNotFoundError) as exc_err:
            EffectivenessMeasures(_config, _analysis)
        assert str(exc_err.value) == str(
            _config["input"] / "direct" / "effectiveness_measures.csv"
        )

    @pytest.mark.parametrize(
        "duration",
        [
            pytest.param(9, id="Less than 10"),
            pytest.param(61, id="More than 60"),
            pytest.param(30, id="Between 10 and 60"),
        ],
    )
    def test_knmi_correction_with_invalid_duration_raises(self, duration: int):
        # 1. Define test data.
        # 2. Run test.
        with pytest.raises(ValueError) as exc_err:
            EffectivenessMeasures.knmi_correction(None, duration)
        # 3. Verify final expectations.
        assert str(exc_err.value) == "Wrong duration configured, has to be 10 or 60"

    @pytest.mark.parametrize(
        "duration",
        [
            pytest.param(10, id="10 minute duration"),
            pytest.param(60, id="60 minute duration"),
        ],
    )
    def test_knmi_correction_with_valid_duration(self, duration: int):
        # 1. Define test data.
        df_data = {"length": 42, "coefficient": {"length": 24, "max": 42}}
        _dataframe = pd.DataFrame(df_data)

        # 2. Run test.
        _correction = EffectivenessMeasures.knmi_correction(_dataframe, duration)

        # 3. Verify final expectations.
        assert isinstance(_correction, pd.DataFrame)

    def test_calculate_effectiveness(self):
        # 1. Define test data.
        _name = "standard"
        df_data = {
            "slope_0015_m": range(0, 4),
            "slope_001_m": range(2, 6),
            "ver_hoger_m": range(4, 8),
            "hwa_afw_ho_m": range(6, 10),
            "gw_hwa_m": range(8, 12),
            "slope_0015_m2": range(10, 14),
            "dichtbij_m": range(12, 16),
            "verkant_max": range(14, 18),
            "verweg_max": range(16, 20),
            "LinkNr": range(18, 22),
            "length": range(20, 24),
            f"{_name}_gevoelig_max": range(22, 26),
            f"{_name}_gevoelig_sum": range(24, 28),
        }
        _dataframe = pd.DataFrame(df_data)

        # 2. Run test.
        _correction = EffectivenessMeasures.calculate_effectiveness(
            _dataframe, "standard"
        )

        # 3. Verify final expectations.
        assert isinstance(_correction, pd.DataFrame)

    def test_calculate_strategy_costs_with_invalid_data_raises(self):
        # 1. Define test data
        _costs_dict = {
            "costs": [2.4, 4.2, 24, 42],
            "on_column": {
                "col_1": "4.2;2.4",
                "col_2": "42;24",
                "col_3": "12;21",
                "col_4": "21;12",
            },
        }
        df_data = {"columns": []}
        _dataframe = pd.DataFrame(df_data)

        # 2. Run test.
        with pytest.raises(ValueError) as exc_err:
            EffectivenessMeasures.calculate_strategy_costs(_dataframe, _costs_dict)

        # 3. Verify expectations.
        assert "Wrong column configured in effectiveness_measures csv file." in str(
            exc_err.value
        )

    def test_calculate_stragey_costs_with_valid_data(self):
        # 1. Define test data
        _costs_dict = {
            "costs": {
                "one_strategy": 1,
                "two_strategies": 2,
            },
            "on_column": {
                "one_strategy": "strategy_a",
                "two_strategies": "strategy_b;strategy_c",
            },
            "npv_factor": 24,
        }
        df_data = {
            "strategy_a": [4.2],
            "strategy_b": [2.4],
            "strategy_c": [42],
            "one_strategy_costs": [0.42],
            "one_strategy_bc_ratio": [1.24],
            "one_strategy_benefits": [1.42],
            "two_strategies_costs": [1.42],
            "two_strategies_bc_ratio": [2.42],
            "two_strategies_benefits": [2.42],
            "reduction_costs_one_strategy": [1],
            "reduction_costs_two_strategies": [2],
        }
        _dataframe = pd.DataFrame(df_data)

        # 2. Run test.
        _costs = EffectivenessMeasures.calculate_strategy_costs(_dataframe, _costs_dict)

        # 3. Verify expectations.
        assert isinstance(_costs, pd.DataFrame)

    @pytest.mark.skip(
        reason="TODO: Is this being used? NPV is deprecated and won't run calc_npv."
    )
    def test_calculate_cost_benefit_analyses(self):
        # 1. Define test data.
        _measures = MockEffectivenessMeasures(None, None)
        _measures.evaluation_period = 1
        _measures.climate_factor = 24
        _measures.interest_rate = 0.42
        _effectiveness_dict = {
            "col_1": {
                "strategy": [42],
                "investment": 2.4,
                "lifespan": 1.0,
                "dichtbij": 0.42,
                "ver_hoger": 4.2,
                "hwa_afw_ho": 42,
                "gw_hwa": 2.4,
                "slope_0015": 24,
                "slope_001": 0.1,
            },
            "1": {
                "lifespan": 1.0,
            },
            "2": {
                "lifespan": 1.0,
            },
        }

        # 2. Run test.
        _measures.cost_benefit_analysis(_effectiveness_dict)

    def test_calculate_cost_reduction(self):
        # 1. Define test data.
        _measures = MockEffectivenessMeasures(None, None)
        _measures.return_period = 1
        _measures.repair_costs = 24
        _measures.interest_rate = 0.42
        _effectiveness_dict = {}
        df_data = {
            "coefficient": 4.2,
            "standard_gevoelig_sum": [42],
            "standard_gevoelig_max": [42.24],
            "return_period": [0.42],
            "blockage_costs_standard": [1.24],
            "blockage_costs": [1.42],
            "yearly_repair_costs_standard": [1.42],
            "repair_costs_standard": [2.42],
            "yearly_blockage_costs_standard": [2.42],
            "max_effectiveness_standard": [1],
            "total_costs_standard": [2],
        }
        _dataframe = pd.DataFrame(df_data)

        # 2. Run test.
        _return_df = _measures.calculate_cost_reduction(_dataframe, _effectiveness_dict)

        # 3. Verify expectations
        assert isinstance(_return_df, pd.DataFrame)
