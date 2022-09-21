from ra2ce.configuration import AnalysisIniConfigData


class TestAnalysisIniConfigData:
    def test_initialize(self):
        _config_data = AnalysisIniConfigData()
        # At this moment it's not really mapped as a FOM.
        assert isinstance(_config_data, dict)
        assert isinstance(_config_data, AnalysisIniConfigData)

    def test_from_dict(self):
        _dict_values = {"the answer": 42}
        _config_data = AnalysisIniConfigData.from_dict(_dict_values)

        assert isinstance(_config_data, AnalysisIniConfigData)
        assert _config_data == _dict_values
