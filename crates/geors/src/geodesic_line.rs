//! GeodesicLine — compute points along a single geodesic.
//!
//! Wraps geographiclib_rs::GeodesicLine.

use crate::geodesic::{DirectResult, Geodesic};

/// Represents a geodesic line for computing multiple positions along the same geodesic.
pub struct GeodesicLine {
    inner: geographiclib_rs::GeodesicLine,
}

impl GeodesicLine {
    /// Create a new geodesic line from a starting point and azimuth.
    pub fn new(geod: &Geodesic, lat1: f64, lon1: f64, azi1: f64) -> Self {
        let inner = geographiclib_rs::GeodesicLine::new(
            geod.inner(),
            lat1,
            lon1,
            azi1,
            None,
            None,
            None,
        );
        GeodesicLine { inner }
    }

    /// Compute position at distance `s12` along the line.
    pub fn position(&self, s12: f64) -> DirectResult {
        let r = self.inner.Position(s12, None);
        DirectResult {
            lat1: *r.get("lat1").unwrap_or(&0.0),
            lon1: *r.get("lon1").unwrap_or(&0.0),
            lat2: *r.get("lat2").unwrap_or(&0.0),
            lon2: *r.get("lon2").unwrap_or(&0.0),
            s12: *r.get("s12").unwrap_or(&s12),
            azi1: *r.get("azi1").unwrap_or(&0.0),
            azi2: *r.get("azi2").unwrap_or(&0.0),
            a12: *r.get("a12").unwrap_or(&0.0),
            ..Default::default()
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::geodesic::wgs84;

    #[test]
    fn test_line_position() {
        let g = wgs84();
        let line = GeodesicLine::new(g, 40.0, -74.0, 45.0);
        let r = line.position(1_000_000.0);
        assert!(r.lat2.abs() <= 90.0);
        assert!(r.lon2.abs() <= 360.0);
    }
}
