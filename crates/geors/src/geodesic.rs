//! Geodesic calculations on an ellipsoid using Karney's algorithm.
//!
//! Wraps geographiclib-rs (a pure Rust port of GeographicLib) and exposes
//! a clean API matching geopy/geographiclib-python semantics.

use geographiclib_rs::{DirectGeodesic, Geodesic as GeodesicInner, InverseGeodesic};

/// Result of the inverse geodesic problem.
#[derive(Clone, Debug, Default)]
pub struct InverseResult {
    pub lat1: f64,
    pub lon1: f64,
    pub lat2: f64,
    pub lon2: f64,
    pub a12: f64,  // angular distance (degrees)
    pub s12: f64,  // distance (meters)
    pub azi1: f64, // forward azimuth at point 1 (degrees)
    pub azi2: f64, // forward azimuth at point 2 (degrees)
    pub m12: f64,  // reduced length (meters)
    pub m_12: f64, // geodesic scale of point 2 relative to point 1
    pub m_21: f64, // geodesic scale of point 1 relative to point 2
    pub s12_area: f64, // area under the geodesic (m^2)
}

/// Result of the direct geodesic problem.
#[derive(Clone, Debug, Default)]
pub struct DirectResult {
    pub lat1: f64,
    pub lon1: f64,
    pub lat2: f64,
    pub lon2: f64,
    pub a12: f64,
    pub s12: f64,
    pub azi1: f64,
    pub azi2: f64,
    pub m12: f64,
    pub m_12: f64,
    pub m_21: f64,
    pub s12_area: f64,
}

/// Geodesic calculator for a given ellipsoid.
pub struct Geodesic {
    inner: GeodesicInner,
    pub a: f64,
    pub f: f64,
    pub(crate) f1: f64,
    pub(crate) b: f64,
    pub(crate) c2: f64,
    pub(crate) ep2: f64,
}

/// Lazy-initialized WGS84 geodesic.
pub fn wgs84() -> &'static Geodesic {
    use std::sync::LazyLock;
    static WGS84: LazyLock<Geodesic> = LazyLock::new(|| {
        Geodesic::new(crate::WGS84_A, crate::WGS84_F)
    });
    &WGS84
}

impl Geodesic {
    /// Create a geodesic calculator for an ellipsoid.
    pub fn new(a: f64, f: f64) -> Self {
        let inner = GeodesicInner::new(a, f);
        let f1 = 1.0 - f;
        let e2 = f * (2.0 - f);
        let ep2 = e2 / (f1 * f1);
        let b = a * f1;
        let c2 = if e2 == 0.0 {
            a * a
        } else if e2 > 0.0 {
            let e = e2.sqrt();
            a * a * (1.0 + (1.0 - e2) / e * e.atanh()) / 2.0
        } else {
            let e = (-e2).sqrt();
            a * a * (1.0 + (1.0 + e2) / e * e.atan()) / 2.0
        };
        Geodesic { inner, a, f, f1, b, c2, ep2 }
    }

    /// Solve the inverse geodesic problem (standard: s12, azi1, azi2, a12).
    pub fn inverse(&self, lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> InverseResult {
        // 4-tuple: (s12, azi1, azi2, a12)
        let (s12, azi1, azi2, a12): (f64, f64, f64, f64) =
            self.inner.inverse(lat1, lon1, lat2, lon2);
        InverseResult {
            lat1, lon1, lat2, lon2,
            s12, azi1, azi2, a12,
            ..Default::default()
        }
    }

    /// Solve the inverse problem with full output.
    pub fn inverse_full(&self, lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> InverseResult {
        // 8-tuple: (s12, azi1, azi2, m12, M12, M21, S12, a12)
        let (s12, azi1, azi2, m12, m_12, m_21, s12_area, a12): (f64, f64, f64, f64, f64, f64, f64, f64) =
            self.inner.inverse(lat1, lon1, lat2, lon2);
        InverseResult {
            lat1, lon1, lat2, lon2,
            s12, azi1, azi2, a12,
            m12, m_12, m_21, s12_area,
        }
    }

    /// Solve the direct geodesic problem (standard: lat2, lon2, azi2).
    pub fn direct(&self, lat1: f64, lon1: f64, azi1: f64, s12: f64) -> DirectResult {
        // 3-tuple: (lat2, lon2, azi2)
        let (lat2, lon2, azi2): (f64, f64, f64) =
            self.inner.direct(lat1, lon1, azi1, s12);
        DirectResult {
            lat1, lon1, lat2, lon2,
            s12, azi1, azi2,
            ..Default::default()
        }
    }

    /// Direct problem with full output.
    pub fn direct_full(&self, lat1: f64, lon1: f64, azi1: f64, s12: f64) -> DirectResult {
        // 8-tuple: (lat2, lon2, azi2, m12, M12, M21, S12, a12)
        let (lat2, lon2, azi2, m12, m_12, m_21, s12_area, a12): (f64, f64, f64, f64, f64, f64, f64, f64) =
            self.inner.direct(lat1, lon1, azi1, s12);
        DirectResult {
            lat1, lon1, lat2, lon2,
            s12, azi1, azi2, a12,
            m12, m_12, m_21, s12_area,
        }
    }

    /// Access the inner geographiclib-rs Geodesic.
    pub fn inner(&self) -> &GeodesicInner {
        &self.inner
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn approx_eq(a: f64, b: f64, tol: f64) -> bool {
        (a - b).abs() < tol
    }

    #[test]
    fn test_wgs84_inverse_basic() {
        let g = wgs84();
        let r = g.inverse(40.6413, -73.7781, 51.4700, -0.4543);
        assert!(
            approx_eq(r.s12 / 1000.0, 5555.0, 50.0),
            "Distance JFK-LHR: {} km",
            r.s12 / 1000.0
        );
    }

    #[test]
    fn test_wgs84_inverse_same_point() {
        let g = wgs84();
        let r = g.inverse(0.0, 0.0, 0.0, 0.0);
        assert_eq!(r.s12, 0.0);
    }

    #[test]
    fn test_wgs84_inverse_antipodal() {
        let g = wgs84();
        let r = g.inverse(0.0, 0.0, 0.0, 180.0);
        assert!(
            approx_eq(r.s12 / 1000.0, 20003.93, 10.0),
            "Antipodal distance: {} km",
            r.s12 / 1000.0
        );
    }

    #[test]
    fn test_wgs84_direct_basic() {
        let g = wgs84();
        let r = g.direct(40.6413, -73.7781, 51.37, 5_554_000.0);
        assert!((r.lat2 - 51.0).abs() < 2.0, "lat2 = {}", r.lat2);
    }

    #[test]
    fn test_direct_inverse_roundtrip() {
        let g = wgs84();
        let d = g.direct(40.0, -74.0, 45.0, 1_000_000.0);
        let inv = g.inverse(40.0, -74.0, d.lat2, d.lon2);
        assert!(
            approx_eq(inv.s12, 1_000_000.0, 0.001),
            "Roundtrip: {} m",
            inv.s12
        );
    }
}
