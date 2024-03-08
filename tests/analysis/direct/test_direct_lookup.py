from collections import OrderedDict

from ra2ce.analyses.direct.direct_lookup import CreateLookupTables, LookUp
from tests import test_data

_lookup_keys = [
    "motorway",
    "trunk",
    "primary",
    "secondary",
    "tertiary",
    "track",
    "other",
    "none",
]


class TestDirectLookUp:
    def test_road_lanes(self):
        _road_lanes = LookUp.road_lanes()
        assert isinstance(_road_lanes, OrderedDict)
        assert all(list(_v.keys()) == _lookup_keys for _v in _road_lanes.values())

    def test_max_damages(self):
        _max_damages = LookUp.max_damages()
        assert isinstance(_max_damages, OrderedDict)
        assert list(_max_damages.keys()) == ["Lower", "Upper"]
        _sorted_keys = sorted(_lookup_keys)
        assert all(
            list(sorted(_v.keys())) == _sorted_keys for _v in _max_damages.values()
        )

    def test_get_max_damages_osd(self):
        _max_damages = LookUp.get_max_damages_osd()
        assert isinstance(_max_damages, OrderedDict)
        assert list(_max_damages.keys()) == ["Lower", "Upper"]
        _sorted_keys = sorted(_lookup_keys)
        assert all(
            list(sorted(_v.keys())) == _sorted_keys for _v in _max_damages.values()
        )


class TestCreateLookupTables:
    def test_create(self):
        # 1. Define test data.
        _settings_file = test_data / "settings" / "OSdaMage_functions.xlsx"
        assert _settings_file.is_file()

        # 2. Run test
        _importer = CreateLookupTables(_settings_file)
        assert _importer.settings_file == _settings_file

        _result = _importer.create()

        # 3. Verify expectations
        _list_results = list(_result)
        assert len(_list_results) == 4
        assert all(isinstance(_lt, OrderedDict) for _lt in _list_results)
