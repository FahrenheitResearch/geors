"""
Drop-in compatibility test: geors vs geopy.

Every test runs the EXACT same code against both geopy.distance and
geors.distance, comparing results. If this passes, geors is a true
drop-in replacement.

Run: pytest tests/test_dropin_compat.py -v
"""

import pytest
import math

# Import both libraries
import geopy.distance as gd
import geors.distance as rd


# ============================================================
# Helper to compare Distance objects
# ============================================================

def assert_distance_eq(geopy_d, geors_d, tol_km=1e-6, label=""):
    """Assert two Distance objects match in all units."""
    assert abs(geopy_d.km - geors_d.km) < tol_km, (
        f"{label}: km: geopy={geopy_d.km}, geors={geors_d.km}, "
        f"diff={abs(geopy_d.km - geors_d.km)}"
    )
    assert abs(geopy_d.miles - geors_d.miles) < tol_km / 1.6, (
        f"{label}: miles mismatch"
    )
    assert abs(geopy_d.meters - geors_d.meters) < tol_km * 1000, (
        f"{label}: meters mismatch"
    )
    assert abs(geopy_d.feet - geors_d.feet) < tol_km * 3281, (
        f"{label}: feet mismatch"
    )
    assert abs(geopy_d.nautical - geors_d.nautical) < tol_km / 1.8, (
        f"{label}: nautical mismatch"
    )


# ============================================================
# 1. Basic distance construction
# ============================================================

class TestBasicDistance:
    """Test Distance class construction and unit conversions."""

    def test_from_km(self):
        gd_d = gd.Distance(1.42)
        rd_d = rd.Distance(1.42)
        assert_distance_eq(gd_d, rd_d, label="from_km")

    def test_from_kwargs(self):
        gd_d = gd.Distance(kilometers=1.42)
        rd_d = rd.Distance(kilometers=1.42)
        assert_distance_eq(gd_d, rd_d, label="from_kwargs_km")

    def test_from_miles(self):
        gd_d = gd.Distance(miles=10)
        rd_d = rd.Distance(miles=10)
        assert_distance_eq(gd_d, rd_d, label="from_miles")

    def test_from_meters(self):
        gd_d = gd.Distance(meters=5000)
        rd_d = rd.Distance(meters=5000)
        assert_distance_eq(gd_d, rd_d, label="from_meters")

    def test_from_feet(self):
        gd_d = gd.Distance(feet=26400)
        rd_d = rd.Distance(feet=26400)
        assert_distance_eq(gd_d, rd_d, label="from_feet")

    def test_from_nautical(self):
        gd_d = gd.Distance(nautical=100)
        rd_d = rd.Distance(nautical=100)
        assert_distance_eq(gd_d, rd_d, label="from_nautical")

    def test_repr(self):
        gd_r = repr(gd.Distance(2.0))
        rd_r = repr(rd.Distance(2.0))
        assert gd_r == rd_r, f"repr: geopy={gd_r}, geors={rd_r}"

    def test_str(self):
        gd_s = str(gd.Distance(2.0))
        rd_s = str(rd.Distance(2.0))
        assert gd_s == rd_s, f"str: geopy={gd_s}, geors={rd_s}"

    def test_float(self):
        # geopy.Distance doesn't implement __float__, but geors does (extra feature)
        # Just verify geors returns km (matching the internal representation)
        rd_f = float(rd.Distance(2.5))
        assert rd_f == 2.5

    def test_bool_true(self):
        assert bool(gd.Distance(1.0)) == bool(rd.Distance(1.0))

    def test_bool_false(self):
        assert bool(gd.Distance(0.0)) == bool(rd.Distance(0.0))

    def test_hash(self):
        assert hash(gd.Distance(1.0)) == hash(rd.Distance(1.0))


# ============================================================
# 2. Arithmetic
# ============================================================

class TestArithmetic:
    def test_add(self):
        gd_r = gd.Distance(2) + gd.Distance(3)
        rd_r = rd.Distance(2) + rd.Distance(3)
        assert_distance_eq(gd_r, rd_r, label="add")

    def test_sub(self):
        gd_r = gd.Distance(5) - gd.Distance(2)
        rd_r = rd.Distance(5) - rd.Distance(2)
        assert_distance_eq(gd_r, rd_r, label="sub")

    def test_neg(self):
        gd_r = -gd.Distance(3)
        rd_r = -rd.Distance(3)
        assert_distance_eq(gd_r, rd_r, label="neg")

    def test_mul(self):
        gd_r = gd.Distance(6) * 5
        rd_r = rd.Distance(6) * 5
        assert_distance_eq(gd_r, rd_r, label="mul")

    def test_rmul(self):
        gd_r = 5 * gd.Distance(6)
        rd_r = 5 * rd.Distance(6)
        assert_distance_eq(gd_r, rd_r, label="rmul")

    def test_truediv_scalar(self):
        gd_r = gd.Distance(6) / 3
        rd_r = rd.Distance(6) / 3
        assert_distance_eq(gd_r, rd_r, label="truediv_scalar")

    def test_truediv_distance(self):
        gd_r = gd.Distance(6) / gd.Distance(2)
        rd_r = rd.Distance(6) / rd.Distance(2)
        assert gd_r == rd_r  # returns a float

    def test_floordiv(self):
        gd_r = gd.Distance(7) // 2
        rd_r = rd.Distance(7) // 2
        assert_distance_eq(gd_r, rd_r, label="floordiv")

    def test_abs(self):
        gd_r = abs(gd.Distance(-3))
        rd_r = abs(rd.Distance(-3))
        assert_distance_eq(gd_r, rd_r, label="abs")

    def test_mul_distance_raises(self):
        with pytest.raises(TypeError):
            gd.Distance(1) * gd.Distance(2)
        with pytest.raises(TypeError):
            rd.Distance(1) * rd.Distance(2)


# ============================================================
# 3. Comparison
# ============================================================

class TestComparison:
    def test_eq(self):
        assert (gd.Distance(2) == gd.Distance(2)) == (rd.Distance(2) == rd.Distance(2))

    def test_ne(self):
        assert (gd.Distance(2) != gd.Distance(3)) == (rd.Distance(2) != rd.Distance(3))

    def test_gt(self):
        assert (gd.Distance(3) > gd.Distance(2)) == (rd.Distance(3) > rd.Distance(2))

    def test_lt(self):
        assert (gd.Distance(2) < gd.Distance(3)) == (rd.Distance(2) < rd.Distance(3))

    def test_ge(self):
        assert (gd.Distance(2) >= gd.Distance(2)) == (rd.Distance(2) >= rd.Distance(2))

    def test_le(self):
        assert (gd.Distance(2) <= gd.Distance(2)) == (rd.Distance(2) <= rd.Distance(2))


# ============================================================
# 4. Geodesic distance between points
# ============================================================

POINT_PAIRS = [
    ((41.49008, -71.312796), (41.499498, -81.695391), "Newport RI -> Cleveland OH"),
    ((-41.32, 174.81), (40.96, -5.50), "Wellington -> Salamanca"),
    ((40.7128, -74.0060), (51.5074, -0.1278), "NYC -> London"),
    ((35.6762, 139.6503), (-33.8688, 151.2093), "Tokyo -> Sydney"),
    ((0, 0), (0, 0), "same point"),
    ((-90, 0), (90, 0), "pole to pole"),
    ((0, 0), (0, 180), "antipodal"),
    ((0, 0), (0.5, 179.5), "near-antipodal (Vincenty fails)"),
]


class TestGeodesicDistance:
    @pytest.mark.parametrize("a,b,desc", POINT_PAIRS)
    def test_two_points(self, a, b, desc):
        gd_d = gd.geodesic(a, b)
        rd_d = rd.geodesic(a, b)
        assert_distance_eq(gd_d, rd_d, tol_km=1e-6, label=desc)

    def test_three_points(self):
        """geodesic(p1, p2, p3) = sum of pairwise distances."""
        p1 = (40.7128, -74.0060)
        p2 = (41.8781, -87.6298)
        p3 = (34.0522, -118.2437)
        gd_d = gd.geodesic(p1, p2, p3)
        rd_d = rd.geodesic(p1, p2, p3)
        assert_distance_eq(gd_d, rd_d, tol_km=1e-6, label="3-point sum")

    def test_four_points(self):
        """Path distance: NYC -> Chicago -> LA -> Seattle."""
        pts = [(40.7128, -74.0060), (41.8781, -87.6298),
               (34.0522, -118.2437), (47.6062, -122.3321)]
        gd_d = gd.geodesic(*pts)
        rd_d = rd.geodesic(*pts)
        assert_distance_eq(gd_d, rd_d, tol_km=1e-6, label="4-point path")

    def test_altitude_equal(self):
        """Equal altitudes should work (altitude ignored)."""
        gd_d = gd.geodesic((40.7128, -74.0060, 100), (51.5074, -0.1278, 100))
        rd_d = rd.geodesic((40.7128, -74.0060, 100), (51.5074, -0.1278, 100))
        assert_distance_eq(gd_d, rd_d, label="equal altitude")

    def test_altitude_different_raises(self):
        """Different altitudes should raise ValueError."""
        with pytest.raises(ValueError):
            gd.geodesic((40.7, -74.0, 0), (51.5, -0.1, 100))
        with pytest.raises(ValueError):
            rd.geodesic((40.7, -74.0, 0), (51.5, -0.1, 100))

    def test_ellipsoid_string(self):
        """Custom ellipsoid by name."""
        gd_d = gd.geodesic((41.49, -71.31), (41.50, -81.70), ellipsoid='GRS-80')
        rd_d = rd.geodesic((41.49, -71.31), (41.50, -81.70), ellipsoid='GRS-80')
        assert_distance_eq(gd_d, rd_d, tol_km=1e-5, label="GRS-80")

    def test_ellipsoid_tuple(self):
        """Custom ellipsoid as tuple (major, minor, flattening)."""
        ell = (6377., 6356., 1 / 297.)
        gd_d = gd.geodesic((41.49, -71.31), (41.50, -81.70), ellipsoid=ell)
        rd_d = rd.geodesic((41.49, -71.31), (41.50, -81.70), ellipsoid=ell)
        assert_distance_eq(gd_d, rd_d, tol_km=1e-5, label="custom ellipsoid")


# ============================================================
# 5. Great circle distance
# ============================================================

class TestGreatCircleDistance:
    @pytest.mark.parametrize("a,b,desc", POINT_PAIRS)
    def test_two_points(self, a, b, desc):
        gd_d = gd.great_circle(a, b)
        rd_d = rd.great_circle(a, b)
        assert_distance_eq(gd_d, rd_d, tol_km=1e-3, label=desc)

    def test_custom_radius(self):
        """Custom sphere radius."""
        gd_d = gd.great_circle((0, 0), (0, 1), radius=6400)
        rd_d = rd.great_circle((0, 0), (0, 1), radius=6400)
        assert_distance_eq(gd_d, rd_d, tol_km=1e-6, label="custom radius")


# ============================================================
# 6. Destination
# ============================================================

class TestDestination:
    def test_geodesic_destination(self):
        """geopy: geodesic(miles=10).destination((34, 148), bearing=90)."""
        gd_pt = gd.geodesic(miles=10).destination((34, 148), bearing=90)
        rd_pt = rd.geodesic(miles=10).destination((34, 148), bearing=90)
        assert abs(gd_pt.latitude - rd_pt.latitude) < 1e-8, (
            f"lat: geopy={gd_pt.latitude}, geors={rd_pt.latitude}"
        )
        assert abs(gd_pt.longitude - rd_pt.longitude) < 1e-8, (
            f"lon: geopy={gd_pt.longitude}, geors={rd_pt.longitude}"
        )

    def test_geodesic_destination_override(self):
        """destination() with distance override."""
        gd_pt = gd.geodesic(miles=10).destination(
            (34, 148), bearing=90, distance=gd.Distance(100)
        )
        rd_pt = rd.geodesic(miles=10).destination(
            (34, 148), bearing=90, distance=rd.Distance(100)
        )
        assert abs(gd_pt.latitude - rd_pt.latitude) < 1e-8
        assert abs(gd_pt.longitude - rd_pt.longitude) < 1e-8

    def test_great_circle_destination(self):
        gd_pt = gd.great_circle(miles=10).destination((34, 148), bearing=90)
        rd_pt = rd.great_circle(miles=10).destination((34, 148), bearing=90)
        assert abs(gd_pt.latitude - rd_pt.latitude) < 1e-6
        assert abs(gd_pt.longitude - rd_pt.longitude) < 1e-6

    def test_destination_returns_point_like(self):
        """destination() should return object with .latitude/.longitude."""
        pt = rd.geodesic(km=100).destination((40, -74), bearing=45)
        assert hasattr(pt, 'latitude')
        assert hasattr(pt, 'longitude')


# ============================================================
# 7. Module-level exports
# ============================================================

class TestExports:
    def test_distance_alias(self):
        assert gd.distance is gd.geodesic
        assert rd.distance is rd.geodesic

    def test_ellipsoids_dict(self):
        for key in gd.ELLIPSOIDS:
            assert key in rd.ELLIPSOIDS, f"Missing ellipsoid: {key}"
            gd_vals = gd.ELLIPSOIDS[key]
            rd_vals = rd.ELLIPSOIDS[key]
            for i in range(3):
                assert abs(gd_vals[i] - rd_vals[i]) < 1e-10, (
                    f"ELLIPSOIDS[{key}][{i}]: geopy={gd_vals[i]}, geors={rd_vals[i]}"
                )

    def test_earth_radius(self):
        assert abs(gd.EARTH_RADIUS - rd.EARTH_RADIUS) < 1e-6

    def test_geodesic_distance_alias(self):
        assert hasattr(rd, 'GeodesicDistance')
        assert rd.GeodesicDistance is rd.geodesic

    def test_great_circle_distance_alias(self):
        assert hasattr(rd, 'GreatCircleDistance')
        assert rd.GreatCircleDistance is rd.great_circle

    def test_lonlat(self):
        gd_pt = gd.lonlat(-71.31, 41.49)
        rd_pt = rd.lonlat(-71.31, 41.49)
        assert abs(gd_pt.latitude - rd_pt.latitude) < 1e-10
        assert abs(gd_pt.longitude - rd_pt.longitude) < 1e-10


# ============================================================
# 8. Real-world workflow: weather station proximity
# ============================================================

class TestRealWorldWorkflow:
    """Simulate a real weather data workflow using both libraries."""

    # ASOS stations near Oklahoma City
    STATIONS = {
        'KOKC': (35.3931, -97.6007),  # Oklahoma City
        'KOUN': (35.2456, -97.4717),  # Norman
        'KTIK': (35.4147, -97.3864),  # Tinker AFB
        'KPWA': (35.5342, -97.6472),  # Wiley Post
        'KSNL': (36.4489, -97.0881),  # Shawnee
        'KGAG': (36.2961, -99.7764),  # Gage
        'KLAW': (34.5678, -98.4167),  # Lawton
        'KSPS': (33.9889, -98.4919),  # Wichita Falls
    }

    def test_distance_matrix(self):
        """Compute all-pairs distance matrix, compare geopy vs geors."""
        stations = list(self.STATIONS.values())
        n = len(stations)

        for i in range(n):
            for j in range(i + 1, n):
                gd_d = gd.geodesic(stations[i], stations[j]).km
                rd_d = rd.geodesic(stations[i], stations[j]).km
                assert abs(gd_d - rd_d) < 1e-6, (
                    f"Station pair ({i},{j}): geopy={gd_d}, geors={rd_d}"
                )

    def test_nearest_station(self):
        """Find nearest station to a tornado report."""
        tornado = (35.22, -97.44)  # Norman, OK

        gd_nearest = min(self.STATIONS.items(),
                         key=lambda s: gd.geodesic(tornado, s[1]).km)
        rd_nearest = min(self.STATIONS.items(),
                         key=lambda s: rd.geodesic(tornado, s[1]).km)
        assert gd_nearest[0] == rd_nearest[0], (
            f"Nearest: geopy={gd_nearest[0]}, geors={rd_nearest[0]}"
        )

    def test_stations_within_radius(self):
        """Find all stations within 100km of a point."""
        center = (35.4, -97.5)
        radius_km = 100

        gd_within = {k for k, v in self.STATIONS.items()
                     if gd.geodesic(center, v).km <= radius_km}
        rd_within = {k for k, v in self.STATIONS.items()
                     if rd.geodesic(center, v).km <= radius_km}
        assert gd_within == rd_within, (
            f"Within {radius_km}km: geopy={gd_within}, geors={rd_within}"
        )

    def test_storm_track_speed(self):
        """Calculate storm motion from two positions."""
        pos1 = (35.20, -97.40)  # 2100Z
        pos2 = (35.50, -97.10)  # 2115Z
        dt_hours = 0.25  # 15 minutes

        gd_dist = gd.geodesic(pos1, pos2).km
        rd_dist = rd.geodesic(pos1, pos2).km

        gd_speed = gd_dist / dt_hours
        rd_speed = rd_dist / dt_hours

        assert abs(gd_speed - rd_speed) < 0.01, (
            f"Storm speed: geopy={gd_speed:.2f}, geors={rd_speed:.2f} km/h"
        )

    def test_path_distance(self):
        """Total path distance through multiple waypoints."""
        path = [
            self.STATIONS['KOKC'],
            self.STATIONS['KOUN'],
            self.STATIONS['KTIK'],
            self.STATIONS['KPWA'],
        ]
        gd_total = gd.geodesic(*path).km
        rd_total = rd.geodesic(*path).km
        assert abs(gd_total - rd_total) < 1e-6, (
            f"Path: geopy={gd_total}, geors={rd_total}"
        )

    def test_destination_from_radar(self):
        """Find point 150km east of radar site."""
        radar = self.STATIONS['KOKC']
        gd_pt = gd.geodesic(kilometers=150).destination(radar, bearing=90)
        rd_pt = rd.geodesic(kilometers=150).destination(radar, bearing=90)
        assert abs(gd_pt.latitude - rd_pt.latitude) < 1e-8
        assert abs(gd_pt.longitude - rd_pt.longitude) < 1e-8
