"""
geors.distance -- drop-in replacement for geopy.distance.

Provides the same API as geopy.distance with Rust-accelerated computation.
All computational functions delegate to Rust via geors._geors.
"""

from geors._geors import distance as _dist
from geors._geors import geodesic as _geo

_geodesic_distance_scalar = _dist.geodesic_distance
_geodesic_destination_scalar = _dist.geodesic_destination
_great_circle_distance_scalar = _dist.great_circle_distance
_great_circle_destination_scalar = _dist.great_circle_destination
geodesic_distance_batch = _dist.geodesic_distance_batch
great_circle_distance_batch = _dist.great_circle_distance_batch

# ============================================================
# Constants (matching geopy.distance exactly)
# ============================================================

EARTH_RADIUS = 6371.009  # IUGG mean earth radius in km

ELLIPSOIDS = {
    # model           major (km)   minor (km)     flattening
    'WGS-84':        (6378.137, 6356.7523142, 1 / 298.257223563),
    'GRS-80':        (6378.137, 6356.7523141, 1 / 298.257222101),
    'Airy (1830)':   (6377.563396, 6356.256909, 1 / 299.3249646),
    'Intl 1924':     (6378.388, 6356.911946, 1 / 297.0),
    'Clarke (1880)': (6378.249145, 6356.51486955, 1 / 293.465),
    'GRS-67':        (6378.1600, 6356.774719, 1 / 298.25),
}


# ============================================================
# Point parsing (matching geopy.point.Point constructor)
# ============================================================

def _to_point(p):
    """Convert various inputs to (lat, lon, alt) matching geopy.point.Point."""
    # Already a Point-like object
    if hasattr(p, 'latitude') and hasattr(p, 'longitude'):
        alt = getattr(p, 'altitude', 0.0)
        return (float(p.latitude), float(p.longitude), float(alt))
    # String
    if isinstance(p, str):
        # Try geopy's Point parser if available
        try:
            from geopy.point import Point
            pt = Point(p)
            return (pt.latitude, pt.longitude, pt.altitude)
        except ImportError:
            raise ValueError(f"String point parsing requires geopy: {p!r}")
    # Tuple/list
    if isinstance(p, (list, tuple)):
        if len(p) == 2:
            return (float(p[0]), float(p[1]), 0.0)
        elif len(p) >= 3:
            return (float(p[0]), float(p[1]), float(p[2]))
        raise ValueError(f"Point must have at least 2 elements, got {len(p)}")
    # Single number -- not a point
    raise TypeError(f"Cannot parse point from {type(p).__name__}: {p!r}")


def _ensure_same_altitude(a, b):
    """Match geopy: raise ValueError if altitudes differ."""
    if abs(a[2] - b[2]) > 1e-6:
        raise ValueError(
            'Calculating distance between points with different altitudes '
            'is not supported'
        )


def _pairwise(iterable):
    """s -> (s0,s1), (s1,s2), ..."""
    it = iter(iterable)
    a = next(it)
    for b in it:
        yield a, b
        a = b


# ============================================================
# Point class (lightweight, for destination returns)
# ============================================================

class Point:
    """Lightweight Point matching geopy.point.Point interface."""

    __slots__ = ('latitude', 'longitude', 'altitude')

    def __init__(self, latitude=0.0, longitude=0.0, altitude=0.0):
        if isinstance(latitude, (list, tuple)):
            if len(latitude) >= 3:
                latitude, longitude, altitude = latitude[0], latitude[1], latitude[2]
            elif len(latitude) >= 2:
                latitude, longitude = latitude[0], latitude[1]
        elif hasattr(latitude, 'latitude'):
            obj = latitude
            longitude = obj.longitude
            altitude = getattr(obj, 'altitude', 0.0)
            latitude = obj.latitude
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.altitude = float(altitude)

    def __repr__(self):
        return f"Point({self.latitude}, {self.longitude}, {self.altitude})"

    def __iter__(self):
        yield self.latitude
        yield self.longitude
        yield self.altitude

    def __getitem__(self, index):
        return (self.latitude, self.longitude, self.altitude)[index]

    def __len__(self):
        return 3

    def __eq__(self, other):
        if isinstance(other, Point):
            return (self.latitude == other.latitude and
                    self.longitude == other.longitude and
                    self.altitude == other.altitude)
        return NotImplemented


def lonlat(x, y, z=0):
    """
    Convert (lon, lat) to Point(lat, lon). Matches geopy.distance.lonlat.

    Example::
        >>> from geors.distance import lonlat, distance
        >>> d = distance(lonlat(-71.312796, 41.49008), lonlat(-81.695391, 41.499498))
    """
    return Point(y, x, z)


# ============================================================
# Unit conversion helpers (matching geopy.units)
# ============================================================

def _km_from_kwargs(kwargs):
    """Extract kilometers from unit keyword arguments."""
    km = kwargs.pop('kilometers', 0)
    km += kwargs.pop('km', 0)
    km += kwargs.pop('meters', 0) / 1000.0
    km += kwargs.pop('m', 0) / 1000.0
    km += kwargs.pop('miles', 0) * 1.609344
    km += kwargs.pop('mi', 0) * 1.609344
    km += kwargs.pop('feet', 0) * 0.0003048
    km += kwargs.pop('ft', 0) * 0.0003048
    km += kwargs.pop('nautical', 0) * 1.852
    km += kwargs.pop('nm', 0) * 1.852
    return km


# ============================================================
# Distance base class (matching geopy.distance.Distance exactly)
# ============================================================

class Distance:
    """
    Base distance class. Stores distance in kilometers (matching geopy).

    Can be created from units::

        >>> Distance(miles=10).km
        16.09344

    Supports comparison, arithmetic, and unit properties.
    """

    def __init__(self, *args, **kwargs):
        kilometers = kwargs.pop('kilometers', 0)
        if len(args) == 1 and isinstance(args[0], (int, float)):
            kilometers += args[0]
        elif len(args) > 1:
            for a, b in _pairwise(args):
                kilometers += self.measure(a, b)
        kilometers += _km_from_kwargs(kwargs)
        self._kilometers = kilometers

    def measure(self, a, b):
        raise NotImplementedError("Distance is an abstract class")

    def destination(self, point, bearing, distance=None):
        raise NotImplementedError("Distance is an abstract class")

    # -- Arithmetic (matching geopy exactly) --

    def __add__(self, other):
        if isinstance(other, Distance):
            return self.__class__(self._kilometers + other._kilometers)
        raise TypeError("Distance instance must be added with Distance instance.")

    def __neg__(self):
        return self.__class__(-self._kilometers)

    def __sub__(self, other):
        return self + -other

    def __mul__(self, other):
        if isinstance(other, Distance):
            raise TypeError("Distance instance must be multiplicated with numbers.")
        return self.__class__(self._kilometers * other)

    def __rmul__(self, other):
        if isinstance(other, Distance):
            raise TypeError("Distance instance must be multiplicated with numbers.")
        return self.__class__(other * self._kilometers)

    def __truediv__(self, other):
        if isinstance(other, Distance):
            return self._kilometers / other._kilometers
        return self.__class__(self._kilometers / other)

    def __floordiv__(self, other):
        if isinstance(other, Distance):
            return self._kilometers // other._kilometers
        return self.__class__(self._kilometers // other)

    def __abs__(self):
        return self.__class__(abs(self._kilometers))

    def __bool__(self):
        return bool(self._kilometers)

    # -- Comparison (matching geopy: compares with Distance or raw number) --

    def __cmp(self, other):
        if isinstance(other, Distance):
            return (self._kilometers > other._kilometers) - (self._kilometers < other._kilometers)
        return (self._kilometers > other) - (self._kilometers < other)

    def __hash__(self):
        return hash(self._kilometers)

    def __eq__(self, other):
        return self.__cmp(other) == 0

    def __ne__(self, other):
        return self.__cmp(other) != 0

    def __gt__(self, other):
        return self.__cmp(other) > 0

    def __lt__(self, other):
        return self.__cmp(other) < 0

    def __ge__(self, other):
        return self.__cmp(other) >= 0

    def __le__(self, other):
        return self.__cmp(other) <= 0

    # -- Representation --

    def __repr__(self):
        return f"Distance({self._kilometers})"

    def __str__(self):
        return f"{self._kilometers} km"

    def __float__(self):
        return float(self._kilometers)

    # -- Unit properties --

    @property
    def kilometers(self):
        return self._kilometers

    @property
    def km(self):
        return self._kilometers

    @property
    def meters(self):
        return self._kilometers * 1000.0

    @property
    def m(self):
        return self.meters

    @property
    def miles(self):
        return self._kilometers / 1.609344

    @property
    def mi(self):
        return self.miles

    @property
    def feet(self):
        return self._kilometers / 0.0003048

    @property
    def ft(self):
        return self.feet

    @property
    def nautical(self):
        return self._kilometers / 1.852

    @property
    def nm(self):
        return self.nautical


# ============================================================
# geodesic (matching geopy.distance.geodesic)
# ============================================================

class geodesic(Distance):
    """
    Geodesic distance using Karney's algorithm. Drop-in replacement
    for geopy.distance.geodesic.

    Supports all geopy calling conventions::

        >>> geodesic((40.7128, -74.0060), (51.5074, -0.1278)).km
        >>> geodesic(p1, p2, p3).km  # sum of pairwise distances
        >>> geodesic(miles=10).destination((34, 148), bearing=90)
        >>> geodesic(p1, p2, ellipsoid='GRS-80').km
    """

    def __init__(self, *args, **kwargs):
        self.ellipsoid_key = None
        self.ELLIPSOID = None
        self._set_ellipsoid(kwargs.pop('ellipsoid', 'WGS-84'))
        super().__init__(*args, **kwargs)

    def _set_ellipsoid(self, ellipsoid):
        if isinstance(ellipsoid, str):
            try:
                self.ELLIPSOID = ELLIPSOIDS[ellipsoid]
                self.ellipsoid_key = ellipsoid
            except KeyError:
                raise Exception("Invalid ellipsoid. See geors.distance.ELLIPSOIDS")
        else:
            self.ELLIPSOID = tuple(ellipsoid)
            self.ellipsoid_key = None

    def measure(self, a, b):
        a = _to_point(a)
        b = _to_point(b)
        _ensure_same_altitude(a, b)
        lat1, lon1 = a[0], a[1]
        lat2, lon2 = b[0], b[1]

        if self.ellipsoid_key == 'WGS-84' or self.ELLIPSOID == ELLIPSOIDS['WGS-84']:
            # Fast path: use Rust WGS84
            return _geodesic_distance_scalar(lat1, lon1, lat2, lon2) / 1000.0
        else:
            # Non-WGS84 ellipsoid: use geographiclib via geopy fallback
            major, minor, f = self.ELLIPSOID
            try:
                from geographiclib.geodesic import Geodesic
                geod = Geodesic(major * 1000.0, f)
                return geod.Inverse(lat1, lon1, lat2, lon2)['s12'] / 1000.0
            except ImportError:
                raise ImportError(
                    "Non-WGS84 ellipsoids require geographiclib. "
                    "Install with: pip install geographiclib"
                )

    def destination(self, point, bearing, distance=None):
        """
        Calculate destination point.

        Matches geopy.distance.geodesic.destination exactly::

            >>> geodesic(miles=10).destination((34, 148), bearing=90)
            Point(33.99987..., 148.17419..., 0.0)

        Returns a Point object.
        """
        pt = _to_point(point)
        lat1, lon1 = pt[0], pt[1]

        if distance is None:
            distance = self
        if isinstance(distance, Distance):
            dist_km = distance.kilometers
        else:
            dist_km = float(distance)

        dist_m = dist_km * 1000.0

        if self.ellipsoid_key == 'WGS-84' or self.ELLIPSOID == ELLIPSOIDS['WGS-84']:
            lat2, lon2 = _geodesic_destination_scalar(lat1, lon1, bearing, dist_m)
        else:
            major, minor, f = self.ELLIPSOID
            try:
                from geographiclib.geodesic import Geodesic as GG
                geod = GG(major * 1000.0, f)
                r = geod.Direct(lat1, lon1, bearing, dist_m)
                lat2, lon2 = r['lat2'], r['lon2']
            except ImportError:
                raise ImportError(
                    "Non-WGS84 ellipsoids require geographiclib."
                )

        return Point(lat2, lon2)

    # Expose set_ellipsoid as public (geopy does)
    set_ellipsoid = _set_ellipsoid


# ============================================================
# great_circle (matching geopy.distance.great_circle)
# ============================================================

class great_circle(Distance):
    """
    Great-circle distance using Haversine formula. Drop-in replacement
    for geopy.distance.great_circle.

    Supports ``radius`` kwarg for custom sphere radius (in km).
    """

    def __init__(self, *args, **kwargs):
        self.RADIUS = kwargs.pop('radius', EARTH_RADIUS)
        super().__init__(*args, **kwargs)

    def measure(self, a, b):
        a = _to_point(a)
        b = _to_point(b)
        _ensure_same_altitude(a, b)

        if abs(self.RADIUS - EARTH_RADIUS) < 1e-6:
            # Fast path: Rust with default radius
            return _great_circle_distance_scalar(a[0], a[1], b[0], b[1]) / 1000.0
        else:
            # Custom radius: compute in Python
            from math import radians, sin, cos, sqrt, atan2
            lat1 = radians(a[0])
            lat2 = radians(b[0])
            dlat = lat2 - lat1
            dlon = radians(b[1] - a[1])
            h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            return self.RADIUS * 2 * atan2(sqrt(h), sqrt(1 - h))

    def destination(self, point, bearing, distance=None):
        """Calculate destination on great circle. Returns Point."""
        pt = _to_point(point)
        lat1, lon1 = pt[0], pt[1]

        if distance is None:
            distance = self
        if isinstance(distance, Distance):
            dist_km = distance.kilometers
        else:
            dist_km = float(distance)

        dist_m = dist_km * 1000.0

        if abs(self.RADIUS - EARTH_RADIUS) < 1e-6:
            lat2, lon2 = _great_circle_destination_scalar(lat1, lon1, bearing, dist_m)
        else:
            from math import radians, degrees, sin, cos, asin, atan2
            lat1r = radians(lat1)
            lon1r = radians(lon1)
            br = radians(bearing)
            d = dist_km / self.RADIUS
            lat2r = asin(sin(lat1r) * cos(d) + cos(lat1r) * sin(d) * cos(br))
            lon2r = lon1r + atan2(sin(br) * sin(d) * cos(lat1r),
                                  cos(d) - sin(lat1r) * sin(lat2r))
            lat2, lon2 = degrees(lat2r), degrees(lon2r)

        return Point(lat2, lon2)


# ============================================================
# Aliases (matching geopy.distance)
# ============================================================

GeodesicDistance = geodesic
GreatCircleDistance = great_circle
distance = geodesic
