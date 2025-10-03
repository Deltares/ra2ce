import shutil
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import Point

from tests import test_data, test_results
from tests.output_validator.output_validator import OutputValidator


class TestOutputValidator:
    def test_run_output_validator_does_not_raise(self) -> None:
        # 1. Define test data.
        _validator = OutputValidator(result_path=test_data.joinpath("simple_inputs"))

        # 2. Run test data.
        _validator.validate_results()

        # 3. Verify expectations.
        # No exception raised means success.

    def test_run_output_validator_unknown_reference_raises(self) -> None:
        # 1. Define test data.
        _unknown_reference = test_data.joinpath("unknown_reference")
        _validator = OutputValidator(
            result_path=test_data.joinpath("simple_inputs"),
            reference_path=_unknown_reference,
        )

        # 2. Run test data and verify expectations.
        with pytest.raises(FileNotFoundError) as exc:
            _validator.validate_results()

        assert str(exc.value) == f"Reference path {_unknown_reference} not found."

    @pytest.fixture(name="results_dir")
    def _get_simple_inputs(self, request: pytest.FixtureRequest) -> Path:
        _test_dir = test_data.joinpath("simple_inputs")
        assert _test_dir.is_dir()

        _results_dir = test_results.joinpath(request.node.name)
        if _results_dir.exists():
            shutil.rmtree(_results_dir)
        _results_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(_test_dir, _results_dir)

        return _results_dir

    def test_run_output_validator_missing_result_raises(
        self, results_dir: Path
    ) -> None:
        # 1. Define test data.
        _missing_file = "missing_file.gpkg"

        _reference_dir = results_dir.joinpath("reference")
        assert _reference_dir.is_dir()

        _reference_file = _reference_dir.joinpath(_missing_file)
        _reference_file.touch()
        assert _reference_file.is_file()

        _validator = OutputValidator(result_path=results_dir)

        # 2. Run test data and verify expectations.
        with pytest.raises(AssertionError) as exc:
            _validator.validate_results()

        assert str(exc.value) == f"Path does not exist: {_missing_file}"

    def test_run_output_validator_unknown_file_type_raises(
        self, results_dir: Path
    ) -> None:
        # 1. Define test data.
        _unknown_extension = ".xyz"
        _unknown_file = results_dir.joinpath(f"unknown_file{_unknown_extension}")
        _unknown_file.touch()

        _reference_dir = results_dir.joinpath("reference")
        assert _reference_dir.is_dir()

        _unknown_reference_file = _reference_dir.joinpath(
            f"unknown_file{_unknown_extension}"
        )
        shutil.copyfile(_unknown_file, _unknown_reference_file)
        assert _unknown_reference_file.is_file()

        _validator = OutputValidator(result_path=results_dir)

        # 2. Run test data and verify expectations.
        with pytest.raises(NotImplementedError) as exc:
            _validator.validate_results()

        assert (
            str(exc.value)
            == f"No validator implemented for file type {_unknown_extension}"
        )

    def test_run_output_validator_different_gpkg_features_raises(
        self, results_dir: Path
    ) -> None:
        # 1. Define test data.
        _modified_reference_file = results_dir.joinpath(
            "reference", "static", "output_graph", "base_graph_edges.gpkg"
        )
        _modified_reference_file.unlink(missing_ok=True)

        _gpd = gpd.GeoDataFrame(
            columns=["geometry"], crs="epsg:4326", data=[Point(1, 1)]
        )
        _gpd.to_file(_modified_reference_file, driver="GPKG")
        assert _modified_reference_file.is_file()

        _validator = OutputValidator(result_path=results_dir)

        # 2. Run test data and verify expectations.
        with pytest.raises(AssertionError) as exc:
            _validator.validate_results()

        assert str(exc.value).endswith("differ in number of features: 1 != 230")

    def test_run_output_validator_different_gpkg_schema_raises(
        self, results_dir: Path
    ) -> None:
        pass
