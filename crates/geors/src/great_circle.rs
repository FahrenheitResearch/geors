//! Great-circle (Haversine) distance and destination on a sphere.
//!
//! Port of geopy's great_circle class.

use crate::constants::EARTH_RADIUS_KM;

/// Great-circle distance between two points using the Haversine formula.
/// Returns distance in meters.
pub fn great_circle_distance(lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> f64 {
    great_circle_distance_with_radius(lat1, lon1, lat2, lon2, EARTH_RADIUS_KM * 1000.0)
}

/// Great-circle distance with a custom sphere radius (in meters).
pub fn great_circle_distance_with_radius(
    lat1: f64,
    lon1: f64,
    lat2: f64,
    lon2: f64,
    radius: f64,
) -> f64 {
    let lat1 = lat1.to_radians();
    let lat2 = lat2.to_radians();
    let dlat = lat2 - lat1;
    let dlon = (lon2 - lon1).to_radians();

    let a = (dlat / 2.0).sin().powi(2) + lat1.cos() * lat2.cos() * (dlon / 2.0).sin().powi(2);
    let c = 2.0 * a.sqrt().asin();

    radius * c
}

/// Great-circle destination point given start, bearing, and distance.
///
/// - `lat1`, `lon1`: starting point in degrees
/// - `bearing`: initial bearing in degrees
/// - `distance`: distance in meters
///
/// Returns `(lat2, lon2)` in degrees.
pub fn great_circle_destination(
    lat1: f64,
    lon1: f64,
    bearing: f64,
    distance: f64,
) -> (f64, f64) {
    great_circle_destination_with_radius(lat1, lon1, bearing, distance, EARTH_RADIUS_KM * 1000.0)
}

/// Great-circle destination with custom sphere radius (in meters).
pub fn great_circle_destination_with_radius(
    lat1: f64,
    lon1: f64,
    bearing: f64,
    distance: f64,
    radius: f64,
) -> (f64, f64) {
    let lat1 = lat1.to_radians();
    let lon1 = lon1.to_radians();
    let brng = bearing.to_radians();
    let d = distance / radius;

    let lat2 = (lat1.sin() * d.cos() + lat1.cos() * d.sin() * brng.cos()).asin();
    let lon2 =
        lon1 + (brng.sin() * d.sin() * lat1.cos()).atan2(d.cos() - lat1.sin() * lat2.sin());

    (lat2.to_degrees(), lon2.to_degrees())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn approx_eq(a: f64, b: f64, tol: f64) -> bool {
        (a - b).abs() < tol
    }

    #[test]
    fn test_great_circle_same_point() {
        let d = great_circle_distance(0.0, 0.0, 0.0, 0.0);
        assert_eq!(d, 0.0);
    }

    #[test]
    fn test_great_circle_equator() {
        // 1 degree along equator ≈ 111.195 km
        let d = great_circle_distance(0.0, 0.0, 0.0, 1.0);
        assert!(
            approx_eq(d / 1000.0, 111.195, 0.5),
            "1 deg equator = {} km",
            d / 1000.0
        );
    }

    #[test]
    fn test_great_circle_antipodal() {
        // Half circumference ≈ 20015.09 km
        let d = great_circle_distance(0.0, 0.0, 0.0, 180.0);
        assert!(
            approx_eq(d / 1000.0, 20015.09, 1.0),
            "Antipodal = {} km",
            d / 1000.0
        );
    }

    #[test]
    fn test_great_circle_destination_roundtrip() {
        let (lat2, lon2) = great_circle_destination(40.0, -74.0, 90.0, 100_000.0);
        let d_back = great_circle_distance(40.0, -74.0, lat2, lon2);
        assert!(
            approx_eq(d_back, 100_000.0, 1.0),
            "roundtrip distance = {}",
            d_back
        );
    }
}
