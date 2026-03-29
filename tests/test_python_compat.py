"""
Verification tests: geors vs geopy.

Compares every computational function against geopy/geographiclib reference
values to ensure numerical parity.
"""

import pytest
import numpy as np

# Reference implementations
from geopy.distance import geodesic as geopy_geodesic
from geopy.distance import great_circle as geopy_great_circle
from geographiclib.geodesic import Geodesic as GeographiclibGeodesic

# Our Rust implementation
from geors.distance import geodesic, great_circle, distance
from geors._geors import distance as _dist
geodesic_distance = _dist.geodesic_distance
great_circle_distance = _dist.great_circle_distance
geodesic_inverse = _dist.geodesic_inverse
geodesic_destination = _dist.geodesic_destination
great_circle_destination = _dist.great_circle_destination
geodesic_distance_batch = _dist.geodesic_distance_batch
great_circle_distance_batch = _dist.great_circle_distance_batch

from geors._geors import geodesic as _geo
inverse = _geo.inverse
direct = _geo.direct
wgs84_a = _geo.wgs84_a
wgs84_f = _geo.wgs84_f


# ============================================================
# Constants
# ============================================================

class TestConstants:
    def test_wgs84_a(self):
        assert wgs84_a() == 6378137.0

    def test_wgs84_f(self):
        assert abs(wgs84_f() - 1 / 298.257223563) < 1e-15


# ============================================================
# Geodesic distance: scalar
# ============================================================

# Test cases: (lat1, lon1, lat2, lon2, description)
POINT_PAIRS = [
    (0.0, 0.0, 0.0, 0.0, "same point"),
    (0.0, 0.0, 0.0, 1.0, "1 deg equator"),
    (40.6413, -73.7781, 51.4700, -0.4543, "JFK to Heathrow"),
    (35.6762, 139.6503, 40.7128, -74.0060, "Tokyo to NYC"),
    (-33.8688, 151.2093, 48.8566, 2.3522, "Sydney to Paris"),
    (90.0, 0.0, -90.0, 0.0, "pole to pole"),
    (0.0, 0.0, 0.0, 180.0, "antipodal equator"),
    (1.0, 2.0, 3.0, 4.0, "small separation"),
    (89.999, 0.0, 89.999, 180.0, "near-polar"),
    (0.0, 0.0, 0.5, 179.5, "nearly antipodal"),
]


class TestGeodesicDistance:
    @pytest.mark.parametrize("lat1,lon1,lat2,lon2,desc", POINT_PAIRS)
    def test_vs_geopy(self, lat1, lon1, lat2, lon2, desc):
        """Geodesic distance matches geopy to <0.1mm."""
        expected = geopy_geodesic((lat1, lon1), (lat2, lon2)).meters
        got = geodesic_distance(lat1, lon1, lat2, lon2)
        assert abs(got - expected) < 1e-4, (
            f"{desc}: expected {expected:.6f} m, got {got:.6f} m, "
            f"diff {abs(got - expected):.2e} m"
        )

    @pytest.mark.parametrize("lat1,lon1,lat2,lon2,desc", POINT_PAIRS)
    def test_vs_geographiclib(self, lat1, lon1, lat2, lon2, desc):
        """Geodesic distance matches geographiclib directly to <0.01mm."""
        g = GeographiclibGeodesic.WGS84
        expected = g.Inverse(lat1, lon1, lat2, lon2)["s12"]
        got = geodesic_distance(lat1, lon1, lat2, lon2)
        assert abs(got - expected) < 1e-5, (
            f"{desc}: expected {expected:.6f} m, got {got:.6f} m, "
            f"diff {abs(got - expected):.2e} m"
        )


class TestGeodesicInverse:
    def test_full_result_keys(self):
        r = geodesic_inverse(40.0, -74.0, 51.0, 0.0)
        for key in ["s12", "azi1", "azi2", "a12", "lat1", "lon1", "lat2", "lon2"]:
            assert key in r, f"Missing key: {key}"

    @pytest.mark.parametrize("lat1,lon1,lat2,lon2,desc", POINT_PAIRS[:5])
    def test_azimuths_vs_geographiclib(self, lat1, lon1, lat2, lon2, desc):
        """Forward/reverse azimuths match geographiclib."""
        g = GeographiclibGeodesic.WGS84
        expected = g.Inverse(lat1, lon1, lat2, lon2)
        got = geodesic_inverse(lat1, lon1, lat2, lon2)
        if expected["s12"] > 0:
            assert abs(got["azi1"] - expected["azi1"]) < 1e-6, f"{desc}: azi1 mismatch"
            assert abs(got["azi2"] - expected["azi2"]) < 1e-6, f"{desc}: azi2 mismatch"


# ============================================================
# Geodesic direct problem
# ============================================================

class TestGeodesicDirect:
    def test_direct_basic(self):
        r = direct(40.0, -74.0, 45.0, 1_000_000.0)
        assert "lat2" in r
        assert "lon2" in r

    @pytest.mark.parametrize("lat1,lon1,azi,dist", [
        (0.0, 0.0, 0.0, 1_000_000.0),
        (0.0, 0.0, 90.0, 1_000_000.0),
        (45.0, -90.0, 45.0, 5_000_000.0),
        (0.0, 0.0, 180.0, 10_000_000.0),
        (-33.0, 151.0, 300.0, 2_000_000.0),
    ])
    def test_direct_vs_geographiclib(self, lat1, lon1, azi, dist):
        g = GeographiclibGeodesic.WGS84
        expected = g.Direct(lat1, lon1, azi, dist)
        got = direct(lat1, lon1, azi, dist)
        assert abs(got["lat2"] - expected["lat2"]) < 1e-8, (
            f"lat2: {got['lat2']} vs {expected['lat2']}"
        )
        assert abs(got["lon2"] - expected["lon2"]) < 1e-8, (
            f"lon2: {got['lon2']} vs {expected['lon2']}"
        )

    def test_direct_inverse_roundtrip(self):
        """Direct then inverse should recover the original distance."""
        g = GeographiclibGeodesic.WGS84
        lat1, lon1, azi1, s12 = 40.0, -74.0, 51.37, 5_554_000.0
        r = direct(lat1, lon1, azi1, s12)
        d_back = geodesic_distance(lat1, lon1, r["lat2"], r["lon2"])
        assert abs(d_back - s12) < 0.01, f"Roundtrip error: {abs(d_back - s12):.6f} m"


# ============================================================
# Great circle distance
# ============================================================

class TestGreatCircleDistance:
    @pytest.mark.parametrize("lat1,lon1,lat2,lon2,desc", POINT_PAIRS)
    def test_vs_geopy(self, lat1, lon1, lat2, lon2, desc):
        """Great-circle distance matches geopy to <1m."""
        expected = geopy_great_circle((lat1, lon1), (lat2, lon2)).meters
        got = great_circle_distance(lat1, lon1, lat2, lon2)
        # Great circle is approximate anyway; 1m tolerance
        assert abs(got - expected) < 1.0, (
            f"{desc}: expected {expected:.2f} m, got {got:.2f} m, "
            f"diff {abs(got - expected):.4f} m"
        )


# ============================================================
# Python wrapper classes
# ============================================================

class TestPythonWrappers:
    def test_geodesic_class(self):
        d = geodesic((40.7128, -74.0060), (51.5074, -0.1278))
        assert d.km > 5000
        assert d.miles > 3000
        assert d.meters > 5_000_000
        assert d.feet > 15_000_000
        assert d.nautical > 2700

    def test_great_circle_class(self):
        d = great_circle((40.7128, -74.0060), (51.5074, -0.1278))
        assert d.km > 5000

    def test_distance_is_geodesic(self):
        assert distance is geodesic

    def test_comparison(self):
        d1 = geodesic((0, 0), (0, 1))
        d2 = geodesic((0, 0), (0, 2))
        assert d1 < d2
        assert d2 > d1

    def test_arithmetic(self):
        d1 = geodesic((0, 0), (0, 1))
        d2 = geodesic((0, 0), (0, 2))
        d3 = d1 + d2
        assert isinstance(d3, type(d1).__bases__[0])  # Distance
        assert d3.meters > 0

    def test_repr(self):
        d = geodesic((0, 0), (0, 1))
        assert "Distance" in repr(d) or "km" in str(d)


# ============================================================
# Batch operations
# ============================================================

class TestBatch:
    def test_geodesic_batch(self):
        n = 1000
        rng = np.random.default_rng(42)
        lat1 = rng.uniform(-90, 90, n)
        lon1 = rng.uniform(-180, 180, n)
        lat2 = rng.uniform(-90, 90, n)
        lon2 = rng.uniform(-180, 180, n)

        result = geodesic_distance_batch(lat1, lon1, lat2, lon2)
        assert result.shape == (n,)
        assert np.all(result >= 0)

        # Spot-check first 10 against scalar
        for i in range(10):
            expected = geodesic_distance(lat1[i], lon1[i], lat2[i], lon2[i])
            assert abs(result[i] - expected) < 1e-6

    def test_great_circle_batch(self):
        n = 1000
        rng = np.random.default_rng(42)
        lat1 = rng.uniform(-90, 90, n)
        lon1 = rng.uniform(-180, 180, n)
        lat2 = rng.uniform(-90, 90, n)
        lon2 = rng.uniform(-180, 180, n)

        result = great_circle_distance_batch(lat1, lon1, lat2, lon2)
        assert result.shape == (n,)
        assert np.all(result >= 0)


# ============================================================
# Geocoder forwarding
# ============================================================

class TestGeocoderForwarding:
    def test_nominatim_import(self):
        """geors.geocoders.Nominatim should forward to geopy."""
        try:
            from geors.geocoders import Nominatim
            from geopy.geocoders import Nominatim as GeopyNominatim
            assert Nominatim is GeopyNominatim
        except ImportError:
            pytest.skip("geopy not installed")


# ============================================================
# Unit conversions
# ============================================================

class TestUnits:
    def test_km_mi_roundtrip(self):
        from geors._geors import units
        assert abs(units.mi_to_km(units.km_to_mi(100.0)) - 100.0) < 1e-10

    def test_m_ft_roundtrip(self):
        from geors._geors import units
        assert abs(units.ft_to_m(units.m_to_ft(100.0)) - 100.0) < 1e-10

    def test_dms(self):
        from geors._geors import units
        dms_to_deg = units.dms_to_deg
        deg_to_dms = units.deg_to_dms
        dd = dms_to_deg(40.0, 45.0, 30.0)
        d, m, s = deg_to_dms(dd)
        assert abs(d - 40.0) < 1e-10
        assert abs(m - 45.0) < 1e-10
        assert abs(s - 30.0) < 1e-6
