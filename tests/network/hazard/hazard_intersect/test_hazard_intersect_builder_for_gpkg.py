from pathlib import Path

import numpy as np
import pytest
from geopandas import GeoDataFrame
from networkx import MultiGraph
from pyproj import CRS
from shapely.geometry import LineString, MultiPolygon, Point, Polygon

from ra2ce.network.hazard.hazard_intersect.hazard_intersect_builder_for_gpkg import (
    HazardIntersectBuilderForGpkg,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_builder(**kwargs) -> HazardIntersectBuilderForGpkg:
    defaults = dict(
        hazard_field_name="intensity",
        hazard_aggregate_wl="mean",
        ra2ce_names=["EV1"],
        hazard_gpkg_files=[],
    )
    defaults.update(kwargs)
    return HazardIntersectBuilderForGpkg(**defaults)


def _make_square_polygon(x0, y0, x1, y1) -> Polygon:
    return Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def _make_hazard_gdf(polygons: list[Polygon], values: list[float], crs="EPSG:4326") -> GeoDataFrame:
    return GeoDataFrame(
        {"intensity": values, "geometry": polygons},
        crs=crs,
    )


def _make_network_gdf(lines: list[LineString], crs="EPSG:4326") -> GeoDataFrame:
    return GeoDataFrame(
        {"geometry": lines},
        crs=crs,
    )


def _make_graph(edges: list[tuple], crs="EPSG:4326") -> MultiGraph:
    """Build a simple MultiGraph with geometry attributes on edges."""
    graph = MultiGraph()
    graph.graph["crs"] = CRS(crs)
    for i, (u, v, line) in enumerate(edges):
        graph.add_edge(u, v, key=i, geometry=line)
    return graph


# ---------------------------------------------------------------------------
# Tests for _validate_and_fix_geometry
# ---------------------------------------------------------------------------

class TestValidateAndFixGeometry:
    def test_valid_geometry_returned_unchanged(self):
        # 1. Define test data.
        geom = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])

        # 2. Run test.
        result = HazardIntersectBuilderForGpkg._validate_and_fix_geometry(geom)

        # 3. Verify expectations.
        assert result is not None
        assert result.is_valid

    def test_invalid_geometry_is_fixed(self):
        # 1. Define test data — bowtie polygon (self-intersecting, invalid).
        geom = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])
        assert not geom.is_valid

        # 2. Run test.
        result = HazardIntersectBuilderForGpkg._validate_and_fix_geometry(geom)

        # 3. Verify expectations.
        assert result is not None
        assert result.is_valid


# ---------------------------------------------------------------------------
# Tests for _explode_multigeometries
# ---------------------------------------------------------------------------

class TestExplodeMultigeometries:
    def test_single_polygon_unchanged(self):
        # 1. Define test data.
        builder = _make_builder()
        gdf = _make_hazard_gdf([_make_square_polygon(0, 0, 1, 1)], [1.0])

        # 2. Run test.
        result = builder._explode_multigeometries(gdf)

        # 3. Verify expectations.
        assert len(result) == 1
        assert "polygon_id" in result.columns
        assert result["polygon_id"].iloc[0] == 1

    def test_multipolygon_is_exploded(self):
        # 1. Define test data.
        builder = _make_builder()
        mp = MultiPolygon([
            _make_square_polygon(0, 0, 1, 1),
            _make_square_polygon(2, 2, 3, 3),
        ])
        gdf = _make_hazard_gdf([mp], [2.5])

        # 2. Run test.
        result = builder._explode_multigeometries(gdf)

        # 3. Verify expectations.
        assert len(result) == 2
        assert list(result["polygon_id"]) == [1, 2]
        assert result.crs == gdf.crs

    def test_polygon_id_is_sequential(self):
        # 1. Define test data.
        builder = _make_builder()
        polys = [_make_square_polygon(i, 0, i + 1, 1) for i in range(3)]
        gdf = _make_hazard_gdf(polys, [1.0, 2.0, 3.0])

        # 2. Run test.
        result = builder._explode_multigeometries(gdf)

        # 3. Verify expectations.
        assert list(result["polygon_id"]) == [1, 2, 3]


# ---------------------------------------------------------------------------
# Tests for _compute_hazard_for_geometry
# ---------------------------------------------------------------------------

class TestComputeHazardForGeometry:
    @pytest.fixture
    def builder_and_tree(self, tmp_path):
        """Return a builder pre-loaded with one hazard polygon covering x=[0,1], y=[0,1]."""
        from shapely.strtree import STRtree

        poly = _make_square_polygon(0, 0, 1, 1)
        hazard_geoms = [poly]
        hazard_values = [3.0]
        tree = STRtree([poly])
        builder = _make_builder(hazard_aggregate_wl="mean")
        return builder, tree, hazard_geoms, hazard_values

    def test_no_intersection_returns_zeros(self, builder_and_tree):
        # 1. Define test data.
        builder, tree, hazard_geoms, hazard_values = builder_and_tree
        line = LineString([(5, 5), (6, 6)])  # far away

        # 2. Run test.
        fraction, value = builder._compute_hazard_for_geometry(line, tree, hazard_geoms, hazard_values)

        # 3. Verify expectations.
        assert fraction == 0
        assert value == 0

    def test_full_intersection_fraction_is_one(self, builder_and_tree):
        # 1. Define test data.
        builder, tree, hazard_geoms, hazard_values = builder_and_tree
        line = LineString([(0, 0.5), (1, 0.5)])  # fully inside polygon

        # 2. Run test.
        fraction, value = builder._compute_hazard_for_geometry(line, tree, hazard_geoms, hazard_values)

        # 3. Verify expectations.
        assert fraction == pytest.approx(1.0)
        assert value == pytest.approx(3.0)

    def test_partial_intersection_fraction(self, builder_and_tree):
        # 1. Define test data.
        builder, tree, hazard_geoms, hazard_values = builder_and_tree
        line = LineString([(0, 0.5), (2, 0.5)])  # half inside, half outside

        # 2. Run test.
        fraction, value = builder._compute_hazard_for_geometry(line, tree, hazard_geoms, hazard_values)

        # 3. Verify expectations.
        assert fraction == pytest.approx(0.5)
        assert value == pytest.approx(3.0)

    @pytest.mark.parametrize("agg,expected", [
        pytest.param("max", 5.0, id="max"),
        pytest.param("min", 2.0, id="min"),
        pytest.param("mean", pytest.approx(3.5), id="mean"),
    ])
    def test_aggregation_methods(self, tmp_path, agg, expected):
        # 1. Define test data — two adjacent polygons each covering half the line.
        from shapely.strtree import STRtree

        poly_a = _make_square_polygon(0, 0, 1, 1)
        poly_b = _make_square_polygon(1, 0, 2, 1)
        hazard_geoms = [poly_a, poly_b]
        hazard_values = [2.0, 5.0]
        tree = STRtree([poly_a, poly_b])
        line = LineString([(0, 0.5), (2, 0.5)])
        builder = _make_builder(hazard_aggregate_wl=agg)

        # 2. Run test.
        fraction, value = builder._compute_hazard_for_geometry(line, tree, hazard_geoms, hazard_values)

        # 3. Verify expectations.
        assert fraction == pytest.approx(1.0)
        assert value == expected

    def test_none_geometry_returns_zeros(self, builder_and_tree):
        # 1. Define test data — pass a None to simulate unfixable geometry.
        from shapely.strtree import STRtree

        builder = _make_builder()
        tree = STRtree([])

        # 2. Run test — Point has zero length, so should return 0, 0.
        fraction, value = builder._compute_hazard_for_geometry(Point(0, 0), tree, [], [])

        # 3. Verify expectations.
        assert fraction == 0
        assert value == 0


# ---------------------------------------------------------------------------
# Tests for _from_geodataframe
# ---------------------------------------------------------------------------

class TestFromGeoDataFrame:
    @pytest.fixture
    def hazard_gpkg(self, tmp_path) -> Path:
        """Write a single hazard polygon to a gpkg file and return its path."""
        poly = _make_square_polygon(0, 0, 1, 1)
        gdf = _make_hazard_gdf([poly], [4.0])
        path = tmp_path / "hazard.gpkg"
        gdf.to_file(path, driver="GPKG")
        return path

    def test_intersecting_line_gets_hazard_value(self, hazard_gpkg):
        # 1. Define test data.
        line = LineString([(0, 0.5), (1, 0.5)])
        network = _make_network_gdf([line])
        builder = _make_builder(hazard_gpkg_files=[hazard_gpkg])

        # 2. Run test.
        result = builder._from_geodataframe(network)

        # 3. Verify expectations.
        assert "EV1_me" in result.columns
        assert "EV1_fr" in result.columns
        assert result["EV1_me"].iloc[0] == pytest.approx(4.0)
        assert result["EV1_fr"].iloc[0] == pytest.approx(1.0)

    def test_non_intersecting_line_gets_zero(self, hazard_gpkg):
        # 1. Define test data.
        line = LineString([(5, 5), (6, 6)])
        network = _make_network_gdf([line])
        builder = _make_builder(hazard_gpkg_files=[hazard_gpkg])

        # 2. Run test.
        result = builder._from_geodataframe(network)

        # 3. Verify expectations.
        assert result["EV1_me"].iloc[0] == 0
        assert result["EV1_fr"].iloc[0] == 0

    def test_index_label_alignment(self, hazard_gpkg):
        # 1. Define test data — GeoDataFrame with non-sequential index (simulates post-filter state).
        lines = [LineString([(0, 0.5), (1, 0.5)]), LineString([(5, 5), (6, 6)])]
        network = _make_network_gdf(lines)
        network.index = [10, 20]  # non-sequential labels
        builder = _make_builder(hazard_gpkg_files=[hazard_gpkg])

        # 2. Run test.
        result = builder._from_geodataframe(network)

        # 3. Verify expectations — hazard value must end up on label 10, not 20.
        assert result.loc[10, "EV1_me"] == pytest.approx(4.0)
        assert result.loc[20, "EV1_me"] == 0

    def test_crs_mismatch_is_handled(self, tmp_path):
        # 1. Define test data — hazard in EPSG:3857, network in EPSG:4326.

        poly_4326 = _make_square_polygon(0, 0, 1, 1)
        hazard_gdf = GeoDataFrame({"intensity": [4.0], "geometry": [poly_4326]}, crs="EPSG:4326")
        hazard_gdf_3857 = hazard_gdf.to_crs("EPSG:3857")
        path = tmp_path / "hazard_3857.gpkg"
        hazard_gdf_3857.to_file(path, driver="GPKG")

        line = LineString([(0, 0.5), (1, 0.5)])
        network = _make_network_gdf([line], crs="EPSG:4326")
        builder = _make_builder(hazard_gpkg_files=[path])

        # 2. Run test.
        result = builder._from_geodataframe(network)

        # 3. Verify expectations — CRS reprojection should yield a non-zero result.
        assert result["EV1_me"].iloc[0] == pytest.approx(4.0)


# ---------------------------------------------------------------------------
# Tests for _from_networkx
# ---------------------------------------------------------------------------

class TestFromNetworkX:
    @pytest.fixture
    def hazard_gpkg(self, tmp_path) -> Path:
        poly = _make_square_polygon(0, 0, 1, 1)
        gdf = _make_hazard_gdf([poly], [4.0])
        path = tmp_path / "hazard.gpkg"
        gdf.to_file(path, driver="GPKG")
        return path

    def test_intersecting_edge_gets_hazard_value(self, hazard_gpkg):
        # 1. Define test data.
        line = LineString([(0, 0.5), (1, 0.5)])
        graph = _make_graph([(0, 1, line)])
        builder = _make_builder(hazard_gpkg_files=[hazard_gpkg])

        # 2. Run test.
        result = builder._from_networkx(graph)

        # 3. Verify expectations.
        edata = result[0][1][0]
        assert "EV1_me" in edata
        assert "EV1_fr" in edata
        assert edata["EV1_me"] == pytest.approx(4.0)
        assert edata["EV1_fr"] == pytest.approx(1.0)

    def test_non_intersecting_edge_gets_zero(self, hazard_gpkg):
        # 1. Define test data.
        line = LineString([(5, 5), (6, 6)])
        graph = _make_graph([(0, 1, line)])
        builder = _make_builder(hazard_gpkg_files=[hazard_gpkg])

        # 2. Run test.
        result = builder._from_networkx(graph)

        # 3. Verify expectations.
        edata = result[0][1][0]
        assert edata["EV1_me"] == 0
        assert edata["EV1_fr"] == 0

    def test_edge_without_geometry_is_skipped(self, hazard_gpkg):
        # 1. Define test data — edge without a geometry attribute.
        graph = MultiGraph()
        graph.graph["crs"] = CRS("EPSG:4326")
        graph.add_edge(0, 1, key=0)  # no geometry
        builder = _make_builder(hazard_gpkg_files=[hazard_gpkg])

        # 2. Run test.
        result = builder._from_networkx(graph)

        # 3. Verify expectations — no hazard attribute written, no crash.
        edata = result[0][1][0]
        assert "EV1_me" not in edata
