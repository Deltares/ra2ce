from pathlib import Path

import pandas as pd
import pytest

from ra2ce.analyses.direct.damage.manual_damage_functions import ManualDamageFunctions
from ra2ce.analyses.direct.damage_calculation.damage_network_events import (
    DamageNetworkEvents,
)
from ra2ce.analyses.direct.damage_calculation.damage_network_return_periods import (
    DamageNetworkReturnPeriods,
)
from tests import test_data

direct_damage_test_data = test_data / "direct_damage"


class TestDirectDamage:
    @pytest.fixture(autouse=False)
    def risk_data_file(self) -> Path:
        _risk_file = direct_damage_test_data / "risk_test_data.csv"
        assert _risk_file.is_file()
        assert _risk_file.exists()
        return _risk_file

    @pytest.fixture(autouse=False)
    def event_input_output(self) -> dict:
        import numpy as np

        file_path = direct_damage_test_data / "NL332.csv"
        raw_data = pd.read_csv(file_path, index_col=0)
        input_cols = [
            "osm_id",
            "infra_type",
            "lanes",
            "bridge",
            "length",
            "length_rp100",
            "val_rp100",
        ]
        test_input = raw_data[input_cols]

        # rework and rename some columns
        test_input["F_EV1_me"] = test_input["val_rp100"] / 100  # from cm to m
        test_input["F_EV1_fr"] = test_input["length_rp100"] / test_input["length"]
        test_input["length"] = test_input["length"] * 1000  # from km to m
        test_input["highway"] = test_input["infra_type"]
        test_input = test_input.drop(
            columns=["val_rp100", "length_rp100", "infra_type"]
        )

        test_output = test_input.copy()
        test_output["dam_HZ_ref"] = raw_data["dam_HZ_rp100"]
        test_output["dam_HZ_ref"] = test_output["dam_HZ_ref"].replace(
            to_replace=0.0, value=np.nan
        )
        test_output["road_type_ref"] = raw_data["road_type"]

        return dict(input=test_input, output=test_output)

    ######################### EVENT-BASED AND HUIZINGA DAMAGE FUNCTION ###############################################
    def test_event_based_damage_calculation_huizinga_stylized(self):
        """A very stylized test with hypothetical data for the Huizinga damage function.

        The rationale behind this test is described in the appendix of the RA2CE documentation document

        Test characteristics:
            Hazard data: event-based, floods
            Damage function: Huizinga
        """

        # SET PARAMETERS AND LOAD REFERENCE DATA
        damage_function = "HZ"
        test_data_path = direct_damage_test_data / "Direct_damage_tests_EV_HZ.xlsx"
        assert test_data_path.is_file()

        road_gdf = pd.read_excel(test_data_path)

        val_cols = [
            col for col in road_gdf.columns if (col[0].isupper() and col[1] == "_")
        ]

        # DO ACTUAL DAMAGE CALCULATION
        event_gdf = DamageNetworkEvents(road_gdf, val_cols)
        event_gdf.main(damage_function=damage_function)

        # CHECK OUTCOMES OF DAMAGE CALCULATIONS
        df = event_gdf.gdf
        df["dam_EV1_HZ"] = df["dam_EV1_HZ"].fillna(
            0
        )  # Fill nans with zeros, like in the reference data
        error_rows = df["ref_damage"] != df["dam_EV1_HZ"]
        df_errors = df[error_rows]

        # EVALUATE THE RESULT OF THE TEST
        assert df_errors.empty, "Test of Huizinga damage functions failed: {}".format(
            df[error_rows]
        )

    @pytest.mark.skip(reason="To do: Needs refining on what needs to be verified.")
    def test_event_based_damage_calculation_huizinga(
        self, event_input_output: pytest.fixture
    ):
        damage_function = "HZ"

        # This test roughly follows the DirectDamage.road_damage() controller in analyses_direct.py
        test_input = event_input_output["input"]
        test_ref_output = event_input_output["output"]

        road_gdf = test_input

        val_cols = [
            col for col in road_gdf.columns if (col[0].isupper() and col[1] == "_")
        ]

        event_gdf = DamageNetworkEvents(road_gdf, val_cols)
        event_gdf.main(damage_function=damage_function)

        ### Some manual corrections, because the RA2CE implementation also calculates damage for bridges, but the
        ### reference model did not.
        bridges = ~test_ref_output["bridge"].isna()  # find all bridges...

        test_output_series = event_gdf.gdf[
            "dam_EV1_HZ"
        ]  # ... and remove data from ra2ce outcomes
        test_output_series[bridges] = 0
        test_output_series = test_output_series.fillna(0)

        reference_output_series = test_ref_output[
            "dam_HZ_ref"
        ]  # ... and remove data from reference outcomes
        reference_output_series[bridges] = 0
        reference_output_series = reference_output_series.fillna(0)

        ### TOT HIER WAS IK GEKOMEN ###
        # similar = test_output_series == reference_output_series
        # differences = ~similar

        pd.testing.assert_series_equal(
            test_output_series,
            reference_output_series,
            check_names=False,
            check_dtype=False,
            rtol=0.1,
        )

        if not test_output_series.equals(reference_output_series):
            comparison2 = test_output_series.eq(reference_output_series, fill_value=0.0)
            mssg = "{} roads are exactly the same\n".format(comparison2.sum())
            mssg += "So {} roads are different\n".format((~comparison2).sum())
            mssg += "Below the 5 first differences\n"
            mssg += "{}\n".format(event_gdf.gdf[~comparison2].head())
            mssg += "{}\n".format(test_ref_output[~comparison2].head())
            mssg += "{}\n".format(event_gdf.gdf[~comparison2])
            assert comparison2.all(), mssg

    def test_event_based_damage_calculation_osdamage_stylized(self):
        """A very stylized test with hypothetical data using the OSdaMage damage function.

        The rationale behind this test is described in the appendix of the RA2CE documentation document

        Test characteristics:
            Hazard data: event-based, floods
            Damage function: OSdaMage
        """

        # SET PARAMETERS AND LOAD REFERENCE DATA
        damage_function = "OSD"
        test_data_path = direct_damage_test_data / "Direct_damage_tests_EV_OSD.xlsx"
        road_gdf = pd.read_excel(test_data_path)

        val_cols = [
            col for col in road_gdf.columns if (col[0].isupper() and col[1] == "_")
        ]

        # DO ACTUAL DAMAGE CALCULATION
        event_gdf = DamageNetworkEvents(road_gdf, val_cols)
        event_gdf.main(damage_function=damage_function)

        # CHECK OUTCOMES OF DAMAGE CALCULATIONS
        df = event_gdf.gdf

        # LOOP OVER THE OSdaMage functions
        for curve in ["C1", "C2", "C3", "C4", "C5", "C6"]:
            # Check lower boundary of the reconstruction/max damage costs
            ra2ce_results_lower = df["dam_{}_EV1".format(curve)].apply(
                lambda x: x[0] if isinstance(x, tuple) else x
            )
            ra2ce_results_lower = ra2ce_results_lower.fillna(0)
            reference_results_lower = df["ref_{}_LOWEST".format(curve)]

            # EVALUATE THE RESULT OF THE TEST USING PANDAS BUILT-IN FUNCTIONALITY
            pd.testing.assert_series_equal(
                ra2ce_results_lower,
                reference_results_lower,
                check_names=False,
                check_dtype=False,
            )

    def _load_manual_damage_function(self):
        manual_damage_functions = ManualDamageFunctions()
        manual_damage_functions.find_damage_functions(
            folder=direct_damage_test_data / "test_damage_functions"
        )
        manual_damage_functions.load_damage_functions()

        fun0 = manual_damage_functions.loaded[0]

        # Check some damage fractions
        assert fun0.prefix == "te"
        assert (
            fun0.damage_fraction.interpolator(1) == 0.42
        )  # At 1 m water depth, Huizinga should return 0.42 fraction damage
        assert (
            fun0.damage_fraction.interpolator(0.75) == (0.25 + 0.42) / 2
        )  # Check linear interpolation

        # Check some max damage values
        md_data = fun0.max_damage.data
        assert md_data.at["motorway", 4] == 550  # euro/km
        assert md_data.at["track", 2] == 150  # euro/km

        return manual_damage_functions

    ######################### EVENT-BASED AND STYLIZED DAMAGE FUNCTION ###############################################
    def test_event_based_damage_calculation_manual_stylized(self):
        """A very stylized test with hypothetical data for a Manual damage function.
        We here manually load precisely the huizinga damage function, so the test is almost similar to
            test_event_based_damage_calculation_huizinga_stylized

        The rationale behind this test is described in the appendix of the RA2CE documentation document

        Test characteristics:
            Hazard data: event-based, floods
            Damage function: manual
        """

        # SET PARAMETERS AND LOAD REFERENCE DATA
        damage_function = "MAN"
        test_data_path = direct_damage_test_data / "Direct_damage_tests_EV_HZ.xlsx"
        road_gdf = pd.read_excel(test_data_path)

        val_cols = [
            col for col in road_gdf.columns if (col[0].isupper() and col[1] == "_")
        ]

        # LOAD DAMAGE FUNCTIONS
        manual_damage_functions = ManualDamageFunctions()
        manual_damage_functions.find_damage_functions(
            folder=direct_damage_test_data / "test_damage_functions"
        )
        manual_damage_functions.load_damage_functions()

        fun0 = manual_damage_functions.loaded[0]
        assert fun0.prefix == "te"

        # DO ACTUAL DAMAGE CALCULATION
        event_gdf = DamageNetworkEvents(road_gdf, val_cols)
        event_gdf.main(
            damage_function=damage_function,
            manual_damage_functions=manual_damage_functions,
        )

        # CHECK OUTCOMES OF DAMAGE CALCULATIONS
        df = event_gdf.gdf
        df["dam_EV1_te"] = df["dam_EV1_te"].fillna(
            0
        )  # Fill nans with zeros, like in the reference data
        error_rows = df["ref_damage"] != df["dam_EV1_te"]
        df_errors = df[error_rows]

        # EVALUATE THE RESULT OF THE TEST
        assert (
            df_errors.empty
        ), "Test of damage calculation using manually loaded damage functions failed: {}".format(
            df[error_rows]
        )

    @pytest.mark.skip(
        reason="To do: Needs refining on what (and how) needs to be verified."
    )
    def test_old_event_based_damage_calculation_manualfunction(
        self, event_input_output: pytest.fixture
    ):
        # Todo: have a look at this test again, to see if the existing issues have been solved
        damage_function = "MAN"

        # This test roughly follows the DirectDamage.road_damage() controller in analyses_direct.py
        test_input = event_input_output["input"]
        test_ref_output = event_input_output["output"]

        road_gdf = test_input

        val_cols = [
            col for col in road_gdf.columns if (col[0].isupper() and col[1] == "_")
        ]

        manual_damage_functions = self._load_manual_damage_function()

        event_gdf = DamageNetworkEvents(road_gdf, val_cols)
        event_gdf.main(
            damage_function=damage_function,
            manual_damage_functions=manual_damage_functions,
        )
        test_output_series = event_gdf.gdf["dam_EV1_te"]
        reference_output_series = test_ref_output["dam_HZ_ref"]

        if not test_output_series.equals(reference_output_series):
            comparison2 = test_output_series.eq(reference_output_series, fill_value=0.0)
            if not comparison2.all():  # all elements are exactly the same
                import numpy as np

                mssg = "{} roads are exactly the same\n".format(comparison2.sum())
                mssg += "So {} roads are different\n".format((~comparison2).sum())
                mssg += "Below the 5 first differences\n"
                mssg += "{}\n".format(event_gdf.gdf[~comparison2].head())
                mssg += "{}\n".format(test_ref_output[~comparison2].head())
                mssg += "We know that manual inserting the HZ damage function may give slightly different results, Therefore, we are now checking if the result is significant"
                print(mssg)
                threshold_rel = (
                    1  # What is the acceptable difference in a relative sense
                )
                threshold_abs = 10  # Absolute acceptable threshold
                percentage_difference = (
                    100
                    * (test_output_series - reference_output_series)
                    / reference_output_series
                )
                absolute_difference = test_output_series - reference_output_series

                # Todo: the difference is so substantial that we have to check damage calculation
                is_relative_different = abs(percentage_difference) > threshold_rel
                is_absolute_different = abs(absolute_difference) > threshold_abs
                is_combined_different = np.logical_and(
                    is_relative_different, is_absolute_different
                )

                if not is_combined_different.all():
                    pd.set_option("display.max_columns", None)
                    mssg = "{} roads are roughly the same \n".format(
                        is_combined_different.sum()
                    )
                    mssg += "So {} roads are significantly different\n".format(
                        (~is_combined_different).sum()
                    )
                    mssg += "Below the 5 first differences:\n"
                    mssg += "... for the result of the test:\n"
                    mssg += "{}\n".format(event_gdf.gdf[is_combined_different].head())
                    mssg += "... and the reference output:\n"
                    mssg += "{}\n".format(test_ref_output[is_combined_different].head())
                    pytest.fail(mssg)

    def test_construct_damage_network_return_periods(self, risk_data_file: Path):
        damage_network = DamageNetworkReturnPeriods.construct_from_csv(
            risk_data_file, sep=";"
        )
        assert (
            type(damage_network) == DamageNetworkReturnPeriods
        ), "Did not construct object of the right type"

    def test_risk_calculation_default(self, risk_data_file: Path):
        damage_network = DamageNetworkReturnPeriods.construct_from_csv(
            risk_data_file, sep=";"
        )
        damage_network.control_risk_calculation(mode="default")
        assert (
            damage_network.gdf["risk"][0] == damage_network.gdf["ref_risk_default"][0]
        )

    def test_risk_calculation_cutoff(self, risk_data_file: Path):
        for rp in [15, 200, 25]:
            damage_network = DamageNetworkReturnPeriods.construct_from_csv(
                risk_data_file, sep=";"
            )
            damage_network.control_risk_calculation(mode="cut_from_{}_year".format(rp))
            test_result = round(damage_network.gdf["risk"][0], 0)
            reference_result = round(
                damage_network.gdf["ref_risk_cut_from_{}_year".format(rp)][0], 0
            )
            assert test_result == reference_result

    def test_risk_calculation_triangle_to_null(self, risk_data_file: Path):
        damage_network = DamageNetworkReturnPeriods.construct_from_csv(
            risk_data_file, sep=";"
        )
        for triangle_rp in [8, 2]:
            damage_network.control_risk_calculation(
                mode="triangle_to_null_{}_year".format(triangle_rp)
            )
            test_result = round(damage_network.gdf["risk"][0], 0)
            reference_result = round(
                damage_network.gdf[
                    "ref_risk_triangle_to_null_{}_year".format(triangle_rp)
                ][0],
                0,
            )
            assert test_result == reference_result
