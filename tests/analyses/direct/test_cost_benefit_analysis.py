import pytest

from ra2ce.analyses.direct.cost_benefit_analysis import EffectivenessMeasures
from tests import test_data


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
