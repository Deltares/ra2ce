from ra2ce.analyses.indirect.origin_closest_destination import OriginClosestDestination


class TestOriginClosestDestination:
    def test_init_with_category(self):
        # 1. Define test data.
        _config_dict = {
            "origins_destinations": dict(
                origins_names="",
                destinations_names="",
                id_name_origin_destination="",
                origin_out_fraction="",
                origin_count="",
                category="dummy_value",
            ),
            "network": dict(file_id=""),
        }
        _analysis = dict(threshold="", weighing="")
        _hazard_names = None

        # 2. Run test.
        _ocd = OriginClosestDestination(
            config=_config_dict, analysis=_analysis, hazard_names=_hazard_names
        )

        # 3. Verify expectations.
        assert isinstance(_ocd, OriginClosestDestination)
        assert _ocd.analysis == _analysis
        assert _ocd.config == _config_dict
        assert _ocd.hazard_names == _hazard_names
        assert _ocd.results_dict == {}
        assert _ocd.destination_key_value == "dummy_value"
